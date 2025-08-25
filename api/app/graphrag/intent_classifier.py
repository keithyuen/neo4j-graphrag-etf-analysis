import structlog
import json
import hashlib
import time
from typing import List, Dict, Any
from app.models.entities import GroundedEntity, IntentResult
from app.services.ollama_service import OllamaService
from app.graphrag.templates.cypher_queries import list_available_intents

logger = structlog.get_logger()

class IntentClassifier:
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.available_intents = list_available_intents()
        # Cache for intent classification results (query_hash -> (result, timestamp))
        self._classification_cache = {}
        self._cache_ttl = 3600  # 1 hour TTL for classifications
        
        self.classification_prompt = """You are an ETF investment analysis assistant. Classify the user's query into ONE of the following intents. Return ONLY a JSON object with the intent key and confidence score.

Available intents:
- etf_exposure_to_company: Questions about how much a SPECIFIC ETF holds of a SPECIFIC COMPANY (e.g., "SPY's exposure to AAPL", "What percent of QQQ is Microsoft?")
- etf_overlap_weighted: Questions about weighted overlap, combined weights, or top shared holdings between TWO ETFs
- etf_overlap_jaccard: Questions about Jaccard similarity, count-based overlap, or percentage of shared holdings between ETFs
- sector_exposure: Questions about sector distribution within a SPECIFIC ETF (e.g., "SPY's tech sector exposure", "QQQ's sector breakdown") - NOT for individual companies
- etfs_by_sector_threshold: Questions asking WHICH ETFs meet sector exposure criteria (like "Which ETFs have 20% tech exposure?")
- top_holdings_subgraph: Questions about top holdings for visualization
- company_rankings: Questions about which ETFs hold a specific company
- general_llm: General questions, financial advice, or topics outside ETF analysis

User Query: "{query}"

Grounded Entities: {entities}

Return JSON format:
{{"intent": "intent_key", "confidence": 0.95}}

Guidelines:
- CRITICAL: If query asks about ONE ETF's exposure to ONE company (e.g., "SPY's exposure to AAPL") → use "etf_exposure_to_company"
- CRITICAL: If query asks "which ETFs" or "what ETFs" with sector criteria → use "etfs_by_sector_threshold"
- CRITICAL: If query asks about a specific ETF's sector exposure (e.g., "SPY's tech exposure") → use "sector_exposure"
- Company symbols like AAPL, MSFT, GOOGL should trigger "etf_exposure_to_company" when paired with an ETF
- Use entity information to improve classification accuracy
- Confidence should be 0.3-1.0 (relaxed threshold for better coverage)
- If multiple intents could apply, choose the most specific one
- Consider the presence of ETF tickers, company symbols, and sector names"""

    async def classify(self, query: str, entities: List[GroundedEntity]) -> IntentResult:
        """
        Classify user intent using LLM with grounded entities and caching.
        Returns IntentResult with intent, confidence, and required parameters.
        """
        # Check cache first
        cache_key = self._get_cache_key(query, entities)
        cached_result = self._get_cached_classification(cache_key)
        if cached_result:
            logger.info("Using cached intent classification", intent=cached_result.intent)
            return cached_result
        
        # Create entity summary for context
        entity_summary = self._create_entity_summary(entities)
        
        # Format prompt
        prompt = self.classification_prompt.format(
            query=query,
            entities=entity_summary
        )
        
        try:
            # Get classification from LLM with performance optimization
            response = await self.ollama.generate(
                prompt=prompt,
                temperature=0.05,  # Even lower for faster, more deterministic responses
                max_tokens=50,     # Reduced tokens for faster generation
                options={
                    'num_predict': 50,
                    'top_k': 10,    # Reduce token selection for speed
                    'top_p': 0.8    # More focused generation
                }
            )
            
            # Parse JSON response
            classification = self._parse_classification_response(response)
            
            # Validate intent exists
            if classification["intent"] not in self.available_intents:
                logger.warning("LLM returned unknown intent", 
                             intent=classification["intent"],
                             available=self.available_intents)
                classification = self._fallback_classification(query, entities)
            
            # Validate intent makes sense given available entities
            elif not self._validate_intent_entity_match(classification["intent"], entities, query):
                logger.warning("LLM intent doesn't match available entities", 
                             intent=classification["intent"],
                             entities=[e.name for e in entities])
                classification = self._fallback_classification(query, entities)
            
            # Get required parameters for this intent
            required_params = self._get_required_parameters(classification["intent"])
            
            result = IntentResult(
                intent=classification["intent"],
                confidence=classification["confidence"],
                entities=entities,
                required_parameters=required_params
            )
            
            logger.info("Intent classified",
                       intent=result.intent,
                       confidence=result.confidence,
                       required_params=len(required_params))
            
            # Cache the result
            self._cache_classification(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error("Intent classification failed", error=str(e), query=query[:100])
            # Fallback to rule-based classification
            return self._fallback_classification(query, entities)
    
    def _create_entity_summary(self, entities: List[GroundedEntity]) -> str:
        """Create a summary of grounded entities for context."""
        if not entities:
            return "No entities found"
        
        summary_parts = []
        
        etfs = [e.name for e in entities if e.type.value == "ETF"]
        if etfs:
            summary_parts.append(f"ETFs: {', '.join(etfs)}")
        
        companies = [e.name for e in entities if e.type.value == "Company"]
        if companies:
            summary_parts.append(f"Companies: {', '.join(companies)}")
        
        sectors = [e.name for e in entities if e.type.value == "Sector"]
        if sectors:
            summary_parts.append(f"Sectors: {', '.join(sectors)}")
        
        numbers = [e.name for e in entities if e.type.value in ["Percent", "Count"]]
        if numbers:
            summary_parts.append(f"Numbers: {', '.join(numbers)}")
        
        return "; ".join(summary_parts) if summary_parts else "No specific entities"
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract intent classification."""
        try:
            # Try to find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                if "intent" in parsed and "confidence" in parsed:
                    return {
                        "intent": parsed["intent"],
                        "confidence": float(parsed["confidence"])
                    }
            
            # If JSON parsing fails, try to extract from text
            return self._extract_from_text(response)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse LLM classification", error=str(e), response=response[:200])
            return self._extract_from_text(response)
    
    def _extract_from_text(self, response: str) -> Dict[str, Any]:
        """Fallback: extract intent from text response."""
        response_lower = response.lower()
        
        # Look for intent keywords in response
        for intent in self.available_intents:
            if intent in response_lower:
                return {"intent": intent, "confidence": 0.7}
        
        # Default fallback
        return {"intent": "sector_exposure", "confidence": 0.5}
    
    def _fallback_classification(self, query: str, entities: List[GroundedEntity]) -> IntentResult:
        """Rule-based fallback classification when LLM fails."""
        query_lower = query.lower()
        
        # Count entity types
        etf_count = sum(1 for e in entities if e.type.value == "ETF")
        company_count = sum(1 for e in entities if e.type.value == "Company")
        sector_count = sum(1 for e in entities if e.type.value == "Sector")
        has_percentage = any(e.type.value == "Percent" for e in entities)
        has_count = any(e.type.value == "Count" for e in entities)
        
        # Rule-based classification
        # Priority: Check for specific patterns first
        # ETF exposure to company (highest priority)
        if etf_count == 1 and company_count == 1 and ("exposure" in query_lower or "hold" in query_lower or "position" in query_lower):
            intent = "etf_exposure_to_company"
            confidence = 0.95
        # "Which ETFs" patterns
        elif ("which etf" in query_lower or "what etf" in query_lower) and company_count >= 1:
            intent = "company_rankings"
            confidence = 0.9
        elif ("which etf" in query_lower or "what etf" in query_lower) and sector_count >= 1:
            intent = "etfs_by_sector_threshold"
            confidence = 0.9
        elif etf_count >= 2 and company_count == 1:
            # Multiple ETFs + one company = company rankings across those ETFs
            intent = "company_rankings"
            confidence = 0.85
        elif etf_count == 1 and company_count == 1:
            intent = "etf_exposure_to_company"
            confidence = 0.85
        elif etf_count == 2 and ("overlap" in query_lower or "similar" in query_lower):
            if "jaccard" in query_lower or "count" in query_lower or "percentage" in query_lower:
                intent = "etf_overlap_jaccard"
            elif "weight" in query_lower or "combined" in query_lower or "top" in query_lower:
                intent = "etf_overlap_weighted"
            else:
                intent = "etf_overlap_weighted"  # Default to weighted
            confidence = 0.8
        elif etf_count == 1 and sector_count >= 1:
            intent = "sector_exposure"
            confidence = 0.8
        elif sector_count >= 1 and has_percentage:
            intent = "etfs_by_sector_threshold"
            confidence = 0.75
        elif company_count == 1 and etf_count == 0:
            intent = "company_rankings"
            confidence = 0.8
        elif has_count and ("top" in query_lower or "holdings" in query_lower):
            intent = "top_holdings_subgraph"
            confidence = 0.75
        else:
            # Default to general LLM for unmatched queries
            intent = "general_llm"
            confidence = 0.8  # High confidence for general fallback
        
        required_params = self._get_required_parameters(intent)
        
        logger.info("Fallback classification used",
                   intent=intent,
                   confidence=confidence,
                   etf_count=etf_count,
                   company_count=company_count)
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            required_parameters=required_params
        )
    
    def _validate_intent_entity_match(self, intent: str, entities: List[GroundedEntity], query: str) -> bool:
        """Validate that the classified intent makes sense given available entities."""
        query_lower = query.lower()
        
        # Count entity types
        etf_count = sum(1 for e in entities if e.type.value == "ETF")
        company_count = sum(1 for e in entities if e.type.value == "Company") 
        sector_count = sum(1 for e in entities if e.type.value == "Sector")
        has_percentage = any(e.type.value == "Percent" for e in entities)
        
        # Validation rules
        if intent == "etf_exposure_to_company":
            # Requires exactly one ETF and one company
            return etf_count == 1 and company_count == 1
        
        elif intent == "etf_overlap_weighted" or intent == "etf_overlap_jaccard":
            # Requires two ETFs
            return etf_count >= 2
            
        elif intent == "sector_exposure":
            # Requires specific ETF for sector analysis, but NOT if there's also a company specified
            # If both ETF and Company are present, it should be etf_exposure_to_company instead
            return etf_count >= 1 and company_count == 0
            
        elif intent == "etfs_by_sector_threshold":
            # Should be used for "which ETFs" queries with sector criteria (not company queries)
            return sector_count >= 1 and company_count == 0 and ("which etf" in query_lower or "what etf" in query_lower or has_percentage)
            
        elif intent == "company_rankings":
            # Requires company but no ETF specified
            return company_count >= 1 and etf_count == 0
            
        elif intent == "general_llm":
            # General LLM can handle any query
            return True
            
        # Default: assume valid
        return True
    
    def _get_required_parameters(self, intent: str) -> List[str]:
        """Get required parameters for a given intent."""
        from app.graphrag.templates.cypher_queries import get_template
        
        try:
            template = get_template(intent)
            return template.required_params
        except ValueError:
            logger.warning("Unknown intent for parameter lookup", intent=intent)
            return []
    
    def _get_cache_key(self, query: str, entities: List[GroundedEntity]) -> str:
        """Generate cache key for query and entities."""
        entity_names = sorted([e.name for e in entities])  # Sort for consistent key
        cache_input = f"{query.lower().strip()}|{','.join(entity_names)}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_cached_classification(self, cache_key: str) -> IntentResult:
        """Get cached classification if valid."""
        if cache_key in self._classification_cache:
            result, timestamp = self._classification_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            else:
                # Remove expired entry
                del self._classification_cache[cache_key]
        return None
    
    def _cache_classification(self, cache_key: str, result: IntentResult) -> None:
        """Cache classification result."""
        # Clean up old entries (simple LRU-like behavior)
        if len(self._classification_cache) > 100:  # Limit cache size
            oldest_key = min(self._classification_cache.keys(), 
                           key=lambda k: self._classification_cache[k][1])
            del self._classification_cache[oldest_key]
        
        self._classification_cache[cache_key] = (result, time.time())