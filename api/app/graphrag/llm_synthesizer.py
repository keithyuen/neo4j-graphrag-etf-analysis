import structlog
from typing import Dict, Any, List
from app.services.ollama_service import OllamaService
from app.models.entities import CypherResult, IntentResult, GroundedEntity
import re

logger = structlog.get_logger()

class LLMSynthesizer:
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        
        self.synthesis_prompt = """You are a professional ETF analyst. Analyze the data and provide investment insights.

User Query: {query}
Intent: {intent}  
Results Summary: {results_summary}

Provide a professional analysis that explains what this data means for investors. Include the specific percentages and explain the investment significance. Use precise financial terminology. Keep response comprehensive yet focused (150-300 words).

Analysis:"""

        self.no_results_responses = [
            "No matching holdings found for the specified parameters. Our database covers SPY, QQQ, IWM, IJH, IVE, and IVW with their complete portfolio compositions. Please verify ticker symbols or try alternative search terms.",
            "The requested ETF exposure data is not available. Consider checking ticker spelling or exploring similar holdings within our supported ETF universe: SPY, QQQ, IWM, IJH, IVE, IVW.",
            "Unable to locate the specified holdings relationship. Our analysis covers major ETF portfolios - please confirm the ETF and company tickers are accurate and currently held."
        ]
    
    async def synthesize(self, query: str, cypher_result: CypherResult, intent_result: IntentResult) -> str:
        """
        Generate natural language answer from query results.
        This is MANDATORY for all /ask responses.
        """
        logger.info("Starting LLM synthesis - step 1")
        
        try:
            row_count = len(cypher_result.rows) if cypher_result.rows else 0
            logger.info("Row count calculated", row_count=row_count)
        except Exception as e:
            logger.error("Row count calculation failed", error=str(e), error_type=type(e).__name__)
            raise e
        
        try:
            if not cypher_result.rows and intent_result.intent != "general_llm":
                return self._get_no_results_response(intent_result.intent)
            logger.info("No results check passed")
        except Exception as e:
            logger.error("No results check failed", error=str(e), error_type=type(e).__name__)
            raise e
        
        try:
            # Create results summary from top rows
            results_summary = self._create_results_summary(cypher_result.rows, intent_result.intent)
            logger.info("Results summary created", summary_length=len(results_summary))
        except Exception as e:
            logger.error("Results summary creation failed", error=str(e), error_type=type(e).__name__)
            raise e
        
        # Generate answer via LLM
        try:
            logger.info("Formatting prompt")
            prompt = self.synthesis_prompt.format(
                query=query,
                intent=intent_result.intent,
                results_summary=results_summary
            )
            logger.info("Prompt formatted successfully", prompt_length=len(prompt))
            
            logger.info("Calling Ollama generate")
            response = await self.ollama.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500
            )
            logger.info("Ollama generate successful", response_length=len(response) if response else 0)
            
            # Validate response contains a number (only for data-driven queries)
            if intent_result.intent != "general_llm" and not self._contains_concrete_number(response):
                response = self._add_concrete_number(response, cypher_result.rows, intent_result.intent)
            logger.info("Number validation successful")
            
            # Ensure response is within word limit
            response = self._ensure_word_limit(response, max_words=400)
            logger.info("Word limit check successful")
            
            logger.info("LLM synthesis completed", 
                       query_length=len(query),
                       response_length=len(response),
                       intent=intent_result.intent,
                       has_concrete_number=self._contains_concrete_number(response))
            
            return response.strip()
            
        except Exception as e:
            logger.error("LLM synthesis step failed", error=str(e), error_type=type(e).__name__)
            # Fallback to deterministic summary
            return self._create_fallback_response(cypher_result.rows, intent_result.intent)
    
    def _create_results_summary(self, rows: List[Dict[str, Any]], intent: str) -> str:
        """Create a structured summary of query results."""
        if intent == "general_llm":
            return "No data query needed. Respond using your knowledge."
        
        if not rows:
            return "No data found."
        
        # Limit to top 5 rows for summary
        top_rows = rows[:5]
        
        # Debug logging to understand data structure
        logger.debug("Creating results summary", 
                    intent=intent, 
                    row_count=len(rows),
                    has_data=bool(top_rows))
        
        if intent == "etf_exposure_to_company":
            return self._summarize_exposure(top_rows)
        elif intent == "etf_overlap_weighted":
            return self._summarize_overlap(top_rows)
        elif intent == "etf_overlap_jaccard":
            return self._summarize_jaccard(top_rows)
        elif intent == "sector_exposure":
            return self._summarize_sectors(top_rows)
        elif intent == "etfs_by_sector_threshold":
            return self._summarize_sector_etfs(top_rows)
        elif intent == "company_rankings":
            return self._summarize_company_rankings(top_rows)
        elif intent == "top_holdings_subgraph":
            return self._summarize_top_holdings(top_rows)
        else:
            # Generic summary
            return f"Query returned {len(rows)} results. Top results: {str(top_rows[:3])}"
    
    def _summarize_exposure(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize ETF exposure results."""
        if not rows:
            return "No exposure data found."
        
        row = rows[0]
        exposure_percent = row.get('exposure_percent', 0)
        etf = row.get('etf_ticker', 'ETF')
        company = row.get('company_name', row.get('c.symbol', 'company'))
        
        # Debug logging to see exactly what data we have
        logger.debug("Summarizing exposure data", 
                    row_keys=list(row.keys()),
                    exposure_percent=exposure_percent,
                    etf_ticker=etf,
                    company=company)
        
        return f"ETF {etf} holds {exposure_percent:.2f}% in {company}."
    
    def _summarize_overlap(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize ETF overlap results."""
        if not rows:
            return "No overlap data found."
        
        total_companies = len(rows)
        top_overlap = rows[0] if rows else {}
        combined_percent = top_overlap.get('combined_percent', 0)
        company_name = top_overlap.get('company_name', 'Unknown')
        
        total_combined = sum(row.get('combined_percent', 0) for row in rows[:10])
        
        return f"Found {total_companies} overlapping holdings with total combined exposure of {total_combined:.2f}%. Top overlap: {company_name} with {combined_percent:.2f}% combined exposure."
    
    def _summarize_jaccard(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize Jaccard overlap results."""
        if not rows:
            return "No Jaccard data found."
        
        row = rows[0]
        intersection = row.get('intersection', 0)
        jaccard = row.get('jaccard_similarity', 0)
        jaccard_percent = row.get('jaccard_percent', jaccard * 100)
        count1 = row.get('count1', 0)
        count2 = row.get('count2', 0)
        
        return f"Jaccard similarity: {jaccard:.4f} ({jaccard_percent:.2f}%). Intersection: {intersection} companies. ETF1 holdings: {count1}, ETF2 holdings: {count2}"
    
    def _summarize_sectors(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize sector exposure results."""
        if not rows:
            return "No sector data found."
        
        total_sectors = len(rows)
        top_sector = rows[0]
        sector_name = top_sector.get('sector', 'Unknown')
        exposure_percent = top_sector.get('exposure_percent', 0)
        
        return f"ETF has exposure to {total_sectors} sectors. Largest sector exposure: {sector_name} at {exposure_percent:.2f}% with {top_sector.get('company_count', 0)} companies."
    
    def _summarize_sector_etfs(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize ETFs by sector threshold results."""
        if not rows:
            return "No ETFs meet the sector threshold criteria."
        
        count = len(rows)
        top_etf = rows[0]
        exposure_percent = top_etf.get('exposure_percent', 0)
        ticker = top_etf.get('ticker', 'Unknown')
        
        return f"Found {count} ETFs meeting sector criteria. Highest exposure: {ticker} at {exposure_percent:.2f}%."
    
    def _summarize_company_rankings(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize company rankings results."""
        if not rows:
            return "No ETF holdings found for this company."
        
        count = len(rows)
        
        # Create a ranked list of all ETFs with their exposure percentages
        holdings = []
        for row in rows:
            ticker = row.get('e.ticker', 'Unknown')
            etf_name = row.get('etf_name', 'Unknown ETF')
            exposure_percent = row.get('exposure_percent', 0)
            holdings.append(f"{ticker} ({etf_name}): {exposure_percent:.2f}%")
        
        holdings_list = ', '.join(holdings[:3])  # Show top 3
        if len(rows) > 3:
            holdings_list += f" and {len(rows) - 3} more"
            
        return f"Company held by {count} ETFs. Rankings: {holdings_list}."
    
    def _summarize_top_holdings(self, rows: List[Dict[str, Any]]) -> str:
        """Summarize top holdings subgraph results."""
        if not rows:
            return "No holdings data found."
        
        count = len(rows)
        # Extract percentages from direct column data
        percentages = []
        companies = []
        for row in rows:
            exposure_percent = row.get('exposure_percent', 0)
            company = row.get('company_name', row.get('c.symbol', 'Unknown'))
            percentages.append(exposure_percent)
            companies.append(company)
        
        total_exposure = sum(percentages) if percentages else 0
        max_exposure = max(percentages) if percentages else 0
        top_company = companies[0] if companies else 'Unknown'
        
        return f"Top {count} holdings include {top_company} ({max_exposure:.2f}%), with total exposure of {total_exposure:.2f}%."
    
    def _contains_concrete_number(self, text: str) -> bool:
        """Check if response contains concrete numbers."""
        number_patterns = [
            r'\d+\.?\d*%',    # Percentages
            r'\$[\d,]+\.?\d*', # Dollar amounts  
            r'\b\d+\.\d+\b',  # Decimal numbers
            r'\b\d+\b'        # Whole numbers
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _add_concrete_number(self, response: str, rows: List[Dict[str, Any]], intent: str) -> str:
        """Add concrete number to response if missing."""
        if not rows:
            return response
        
        # Extract first numerical value from results
        first_row = rows[0]
        added_number = False
        
        for key, value in first_row.items():
            if isinstance(value, (int, float)) and value > 0 and not added_number:
                if 'percent' in key.lower() or 'exposure_percent' in key.lower():
                    # This is already a percentage value
                    response += f" ({value:.2f}%)"
                    added_number = True
                elif 'count' in key.lower():
                    response += f" (Count: {int(value)})"
                    added_number = True
        
        return response
    
    def _ensure_word_limit(self, response: str, max_words: int = 400) -> str:
        """Ensure response is within word limit, trying to end at sentence boundaries."""
        words = response.split()
        if len(words) <= max_words:
            return response
        
        # Try to find a good sentence ending within the limit
        truncated_text = ' '.join(words[:max_words])
        
        # Look for the last sentence-ending punctuation
        for punct in ['. ', '! ', '? ']:
            last_punct = truncated_text.rfind(punct)
            if last_punct > len(truncated_text) * 0.7:  # Only if it's reasonably near the end
                return truncated_text[:last_punct + 1]
        
        # If no good sentence break found, truncate at word boundary without "..."
        return truncated_text
    
    def _create_fallback_response(self, rows: List[Dict[str, Any]], intent: str) -> str:
        """Create fallback response when LLM fails."""
        if intent == "general_llm":
            return "I'm unable to process general questions at the moment. Please try asking about ETF analysis instead."
            
        if not rows:
            return "No results found for this query."
        
        count = len(rows)
        intent_readable = intent.replace('_', ' ').title()
        
        # Try to extract a key number from first result
        first_row = rows[0]
        key_number = ""
        
        for key, value in first_row.items():
            if isinstance(value, (int, float)) and value > 0:
                if 'weight' in key.lower():
                    key_number = f" with key weight of {value:.4f} ({value*100:.2f}%)"
                    break
                elif 'count' in key.lower():
                    key_number = f" showing {int(value)} items"
                    break
        
        return f"Analysis complete: Found {count} data points for {intent_readable}{key_number}. The results provide specific ETF exposure metrics and portfolio composition details that can inform your investment decisions."
    
    def _get_no_results_response(self, intent: str) -> str:
        """Get appropriate no-results response based on intent."""
        return self.no_results_responses[0]  # Use first response for consistency
    
    async def synthesize_with_comprehensive_data(
        self, 
        query: str, 
        cypher_result: CypherResult, 
        intent_result: IntentResult,
        entities: List[GroundedEntity]
    ) -> str:
        """
        Enhanced synthesis with comprehensive ETF data context.
        Always provides rich context from comprehensive data.
        """
        # Create comprehensive context summary
        comprehensive_summary = self._create_comprehensive_summary(cypher_result)
        
        # Create entity context
        entity_context = self._create_entity_context(entities)
        
        # Enhanced prompt with comprehensive data
        enhanced_prompt = f"""You are a senior ETF strategist with comprehensive market intelligence. Provide expert analysis that transforms data into actionable investment insights.

User Query: {query}
Intent Classification: {intent_result.intent} (confidence: {intent_result.confidence:.2f})
Relevant Entities: {entity_context}

Comprehensive ETF Intelligence:
{comprehensive_summary}

STRATEGIC ANALYSIS FRAMEWORK:
- Synthesize data into clear investment implications and portfolio insights
- Quantify concentration risks, diversification benefits, and sector exposures
- Provide comparative context across ETFs with specific percentages
- Highlight market positioning and competitive advantages/disadvantages
- Identify potential correlation risks or diversification opportunities
- Address liquidity, volatility, and risk-adjusted return considerations when relevant
- Use professional investment terminology with practical applications
- Structure insights for both tactical allocation and strategic planning
- Deliver 200-400 words of comprehensive, high-value analysis

Professional Investment Analysis:"""
        
        try:
            response = await self.ollama.generate(
                prompt=enhanced_prompt,
                temperature=0.2,
                max_tokens=600
            )
            
            # Ensure response contains concrete numbers
            if not self._contains_concrete_number(response):
                response = self._add_concrete_number_from_comprehensive(response, cypher_result)
            
            # Ensure word limit
            response = self._ensure_word_limit(response, 500)  # Higher limit for comprehensive responses
            
            logger.info("Comprehensive LLM synthesis completed", 
                       query_length=len(query),
                       response_length=len(response),
                       intent=intent_result.intent,
                       confidence=intent_result.confidence,
                       has_comprehensive_data=hasattr(cypher_result, 'is_comprehensive_fallback'))
            
            return response.strip()
            
        except Exception as e:
            logger.error("Comprehensive LLM synthesis failed", error=str(e), intent=intent_result.intent)
            # Fallback to regular synthesis
            return await self.synthesize(query, cypher_result, intent_result)
    
    def _create_comprehensive_summary(self, cypher_result: CypherResult) -> str:
        """Create summary of comprehensive ETF data."""
        if not cypher_result.rows:
            return "No comprehensive data available."
        
        # Handle comprehensive data structure
        summary_parts = []
        etf_count = len(cypher_result.rows)
        
        summary_parts.append(f"Available ETFs: {etf_count}")
        
        # Summarize each ETF's key data
        for i, etf_data in enumerate(cypher_result.rows[:6]):  # Limit to top 6 ETFs for context
            etf_ticker = etf_data.get('etf_ticker', f'ETF_{i+1}')
            etf_name = etf_data.get('etf_name', 'Unknown ETF')
            total_holdings = etf_data.get('total_holdings', 0)
            
            # Get top holdings
            holdings = etf_data.get('holdings', [])
            top_holdings = holdings[:5] if holdings else []
            holdings_summary = ", ".join([
                f"{h.get('symbol', 'UNK')} ({h.get('exposure_percent', 0):.1f}%)" 
                for h in top_holdings
            ])
            
            # Get sector distribution
            sectors = etf_data.get('sectors', [])
            top_sectors = sorted(sectors, key=lambda x: x.get('weight', 0), reverse=True)[:3]
            sector_summary = ", ".join([
                f"{s.get('sector', 'Unknown')} ({s.get('weight', 0):.1f}%)" 
                for s in top_sectors
            ])
            
            etf_summary = f"\n{etf_ticker} ({etf_name}): {total_holdings} holdings. "
            etf_summary += f"Top holdings: {holdings_summary}. "
            etf_summary += f"Top sectors: {sector_summary}."
            
            summary_parts.append(etf_summary)
        
        return "\n".join(summary_parts)
    
    def _create_entity_context(self, entities: List[GroundedEntity]) -> str:
        """Create context summary from grounded entities."""
        if not entities:
            return "None specified"
        
        etfs = [e.name for e in entities if e.type.value == 'ETF']
        companies = [e.name for e in entities if e.type.value == 'Company']
        sectors = [e.name for e in entities if e.type.value == 'Sector']
        
        context_parts = []
        if etfs:
            context_parts.append(f"ETFs: {', '.join(etfs)}")
        if companies:
            context_parts.append(f"Companies: {', '.join(companies)}")
        if sectors:
            context_parts.append(f"Sectors: {', '.join(sectors)}")
        
        return "; ".join(context_parts) if context_parts else "None specified"
    
    def _add_concrete_number_from_comprehensive(self, response: str, cypher_result: CypherResult) -> str:
        """Add concrete numbers from comprehensive data if missing."""
        if not cypher_result.rows:
            return response
        
        # Try to add a meaningful number from the comprehensive data
        first_etf = cypher_result.rows[0]
        holdings = first_etf.get('holdings', [])
        
        if holdings:
            top_holding = holdings[0]
            exposure = top_holding.get('exposure_percent', 0)
            symbol = top_holding.get('symbol', 'top holding')
            response += f" (Top holding: {symbol} at {exposure:.2f}%)"
        else:
            total_holdings = first_etf.get('total_holdings', 0)
            response += f" (Total holdings analyzed: {total_holdings})"
        
        return response