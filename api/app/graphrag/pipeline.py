import time
import hashlib
import json
import structlog
from typing import Dict, Any, Optional
from app.models.entities import GroundedEntity, IntentResult, ParameterFulfillment, CypherResult
from app.models.responses import GraphRAGResponse, ResponseMetadata
from app.services.neo4j_service import Neo4jService
from app.services.ollama_service import OllamaService
from .preprocessor import Preprocessor
from .entity_grounder import EntityGrounder
from .intent_classifier import IntentClassifier
from .parameter_fulfiller import ParameterFulfiller
from .cypher_executor import CypherExecutor
from .llm_synthesizer import LLMSynthesizer

logger = structlog.get_logger()

class GraphRAGPipeline:
    def __init__(self, neo4j_service: Neo4jService, ollama_service: OllamaService):
        self.neo4j = neo4j_service
        self.ollama = ollama_service
        
        # Initialize pipeline components
        self.preprocessor = Preprocessor()
        self.entity_grounder = EntityGrounder(neo4j_service)
        self.intent_classifier = IntentClassifier(ollama_service)
        self.parameter_fulfiller = ParameterFulfiller(neo4j_service)
        self.cypher_executor = CypherExecutor(neo4j_service)
        self.llm_synthesizer = LLMSynthesizer(ollama_service)
        
        # Caching
        self._comprehensive_data_cache: Optional[CypherResult] = None
        self._comprehensive_data_cache_time: float = 0
        self._comprehensive_cache_ttl = 36000  # 10 hour TTL
        self._response_cache: Dict[str, tuple] = {}  # query_hash -> (response, timestamp)
        self._response_cache_ttl = 18000  # 5 hour TTL
    
    async def process_query(self, query: str) -> GraphRAGResponse:
        """
        Execute the complete 7-step GraphRAG pipeline with relaxed classification.
        Always provides comprehensive data context for better LLM synthesis.
        """
        start_time = time.time()
        timing = {}
        
        # Note: Cache check moved after entity grounding and intent classification 
        # to create a more accurate cache key that includes intent and entities
        
        logger.info("Starting GraphRAG pipeline (relaxed mode)", query=query[:100])
        
        try:
            # Step 1: Preprocessing
            step_start = time.time()
            preprocessed = await self.preprocessor.process(query)
            timing['preprocessing'] = time.time() - step_start
            
            # Step 2: Entity Grounding
            step_start = time.time()
            entities = await self.entity_grounder.ground_entities(preprocessed)
            timing['entity_grounding'] = time.time() - step_start
            
            # Step 3: Intent Classification (Relaxed)
            step_start = time.time()
            intent_result = await self.intent_classifier.classify(query, entities)
            timing['intent_classification'] = time.time() - step_start
            
            # Step 4: Parameter Fulfillment (Relaxed - allow partial completion)
            step_start = time.time()
            param_result = await self.parameter_fulfiller.fulfill(intent_result, entities)
            timing['parameter_fulfillment'] = time.time() - step_start
            
            # Check response cache after intent and entity grounding for accurate cache key
            query_hash = self._get_query_hash_with_context(query, intent_result, entities, param_result)
            cached_response = self._get_cached_response(query_hash)
            if cached_response:
                logger.info("Using cached response with context-aware key", 
                           intent=intent_result.intent, 
                           entities_count=len(entities))
                return cached_response
            
            # Step 5: Comprehensive Data Fetch + Specific Query
            step_start = time.time()
            
            # Only fetch comprehensive data if we don't have specific params or low confidence
            comprehensive_data = None
            specific_result = None
            
            # Try specific query first if we have complete parameters and high confidence
            if param_result.is_complete and intent_result.confidence > 0.6 and intent_result.intent != "general_llm":
                try:
                    specific_result = await self.cypher_executor.execute(
                        intent_result.intent, param_result.parameters
                    )
                    logger.info("Specific query succeeded", 
                               intent=intent_result.intent, 
                               rows=len(specific_result.rows) if specific_result.rows else 0)
                except Exception as e:
                    logger.warning("Specific query failed, will fallback to comprehensive data", 
                                 intent=intent_result.intent, error=str(e))
            
            # Determine final result strategy
            if specific_result and specific_result.rows:
                # Use specific results - no comprehensive data needed
                cypher_result = specific_result
                logger.info("Using specific query results", rows=len(specific_result.rows))
            else:
                # Fallback to comprehensive data (with caching)
                logger.info("Falling back to comprehensive data")
                comprehensive_data = await self._get_cached_comprehensive_data()
                if not comprehensive_data:
                    comprehensive_data = await self.cypher_executor.execute("comprehensive_data", {})
                    await self._cache_comprehensive_data(comprehensive_data)
                
                cypher_result = comprehensive_data
                cypher_result.is_comprehensive_fallback = True
                
            timing['cypher_execution'] = time.time() - step_start
            
            # Step 6: LLM Synthesis (choose method based on data type)
            step_start = time.time()
            
            # Use appropriate synthesis method based on data source
            if hasattr(cypher_result, 'is_comprehensive_fallback') and cypher_result.is_comprehensive_fallback:
                # Using comprehensive data as fallback - use enhanced synthesis
                logger.info("Using comprehensive synthesis method", 
                           rows_count=len(cypher_result.rows), 
                           has_fallback_flag=True)
                llm_answer = await self.llm_synthesizer.synthesize_with_comprehensive_data(
                    query, cypher_result, intent_result, entities
                )
            else:
                # Have specific query results - use regular synthesis
                logger.info("Using regular synthesis method", 
                           rows_count=len(cypher_result.rows), 
                           has_fallback_flag=False)
                llm_answer = await self.llm_synthesizer.synthesize(
                    query, cypher_result, intent_result
                )
            timing['llm_synthesis'] = time.time() - step_start
            
            # Step 7: Response Assembly
            total_time = time.time() - start_time
            timing['total_pipeline'] = total_time
            
            metadata = ResponseMetadata(
                timing=timing,
                cache_hit=False,  # Will be set to True for cached responses
                confidence=intent_result.confidence,
                node_count=cypher_result.node_count,
                edge_count=cypher_result.edge_count
            )
            
            response = GraphRAGResponse(
                answer=llm_answer,
                rows=cypher_result.rows,
                intent=intent_result.intent,
                cypher=cypher_result.query,
                entities=entities,
                metadata=metadata
            )
            
            # Cache the response with context-aware key
            self._cache_response(query_hash, response)
            
            # Enhanced performance logging
            performance_metrics = {
                'intent': intent_result.intent,
                'total_time_ms': round(total_time * 1000, 2),
                'total_time_category': 'fast' if total_time < 5 else 'slow' if total_time < 30 else 'very_slow',
                'result_count': len(cypher_result.rows),
                'has_llm_answer': bool(llm_answer),
                'used_comprehensive_fallback': hasattr(cypher_result, 'is_comprehensive_fallback'),
                'cached_comprehensive_data': bool(self._comprehensive_data_cache),
                'confidence': intent_result.confidence,
                'step_times': {k: round(v * 1000, 2) for k, v in timing.items()},
                'performance_bottleneck': max(timing.keys(), key=lambda k: timing.get(k, 0))
            }
            
            logger.info("GraphRAG pipeline completed successfully", **performance_metrics)
            
            return response
            
        except Exception as e:
            logger.error("GraphRAG pipeline failed", error=str(e), query=query[:100])
            # Return error response with fallback answer
            return self._create_error_response(query, str(e), time.time() - start_time)
    
    def _create_missing_params_response(
        self, 
        query: str, 
        intent_result: IntentResult, 
        entities: list, 
        param_result: ParameterFulfillment,
        timing: Dict[str, float]
    ) -> GraphRAGResponse:
        """Create response for queries with missing parameters."""
        missing_params_msg = self._generate_missing_params_message(
            intent_result.intent, param_result.missing_parameters
        )
        
        timing['total_pipeline'] = sum(timing.values())
        
        metadata = ResponseMetadata(
            timing=timing,
            cache_hit=False,
            confidence=intent_result.confidence
        )
        
        return GraphRAGResponse(
            answer=missing_params_msg,
            rows=[],
            intent=intent_result.intent,
            cypher="",
            entities=entities,
            metadata=metadata
        )
    
    def _create_error_response(self, query: str, error: str, total_time: float) -> GraphRAGResponse:
        """Create response for pipeline errors."""
        metadata = ResponseMetadata(
            timing={'total_pipeline': total_time, 'error': True},
            cache_hit=False,
            confidence=0.0
        )
        
        return GraphRAGResponse(
            answer=f"Sorry, I encountered an error processing your query. Please try rephrasing your question or check that you're using valid ETF tickers and company symbols.",
            rows=[],
            intent="error",
            cypher="",
            entities=[],
            metadata=metadata
        )
    
    def _generate_missing_params_message(self, intent: str, missing_params: list) -> str:
        """Generate helpful message for missing parameters."""
        param_hints = {
            "ticker": "Please specify an ETF ticker (SPY, QQQ, IWM, IJH, IVE, IVW)",
            "ticker1": "Please specify the first ETF ticker",
            "ticker2": "Please specify the second ETF ticker for comparison",
            "symbol": "Please specify a company ticker symbol (e.g., AAPL, MSFT, GOOGL)",
            "sector": "Please specify a sector name (e.g., Technology, Healthcare, Financials)",
            "threshold": "Please specify a percentage threshold (e.g., 5%, 10%)",
            "top_n": "Please specify how many top holdings to show"
        }
        
        hints = []
        for param in missing_params:
            hint = param_hints.get(param, f"Please provide {param}")
            hints.append(hint)
        
        if len(hints) == 1:
            return f"To complete your query, I need additional information: {hints[0]}."
        else:
            return f"To complete your query, I need additional information: {', '.join(hints[:-1])}, and {hints[-1]}."
    
    def _get_query_hash(self, query: str) -> str:
        """Generate hash for query caching (legacy method - kept for compatibility)."""
        # Normalize query for caching (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    def _get_query_hash_with_context(self, query: str, intent_result, entities, param_result) -> str:
        """Generate context-aware hash for query caching that includes intent and entities."""
        from app.models.entities import IntentResult, ParameterFulfillment, GroundedEntity
        
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Include intent
        intent = intent_result.intent if intent_result else "unknown"
        
        # Include sorted entity names and types for consistency
        entity_signature = []
        if entities:
            for entity in sorted(entities, key=lambda x: x.name):
                entity_signature.append(f"{entity.type.value}:{entity.name}")
        entity_str = "|".join(entity_signature)
        
        # Include sorted parameter keys and values for consistency
        param_signature = []
        if param_result and param_result.parameters:
            for key in sorted(param_result.parameters.keys()):
                value = param_result.parameters[key]
                param_signature.append(f"{key}={value}")
        param_str = "|".join(param_signature)
        
        # Create composite cache key
        cache_input = f"query:{normalized_query}|intent:{intent}|entities:{entity_str}|params:{param_str}"
        
        logger.debug("Generating context-aware cache key", 
                    query_preview=normalized_query[:50],
                    intent=intent,
                    entities_count=len(entities) if entities else 0,
                    params_count=len(param_result.parameters) if param_result and param_result.parameters else 0,
                    cache_key_preview=cache_input[:100])
        
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_time: float, ttl: int) -> bool:
        """Check if cache is still valid."""
        return time.time() - cache_time < ttl
    
    async def _get_cached_comprehensive_data(self) -> Optional[CypherResult]:
        """Get cached comprehensive data if valid."""
        if (self._comprehensive_data_cache and 
            self._is_cache_valid(self._comprehensive_data_cache_time, self._comprehensive_cache_ttl)):
            logger.info("Using cached comprehensive data")
            return self._comprehensive_data_cache
        return None
    
    async def _cache_comprehensive_data(self, data: CypherResult) -> None:
        """Cache comprehensive data."""
        self._comprehensive_data_cache = data
        self._comprehensive_data_cache_time = time.time()
        logger.info("Cached comprehensive data", rows_count=len(data.rows))
    
    def _get_cached_response(self, query_hash: str) -> Optional[GraphRAGResponse]:
        """Get cached response if valid."""
        if query_hash in self._response_cache:
            response, cache_time = self._response_cache[query_hash]
            if self._is_cache_valid(cache_time, self._response_cache_ttl):
                logger.info("Using cached response", query_hash=query_hash)
                # Update metadata to indicate cache hit
                response.metadata.cache_hit = True
                return response
            else:
                # Remove expired cache entry
                del self._response_cache[query_hash]
        return None
    
    def _cache_response(self, query_hash: str, response: GraphRAGResponse) -> None:
        """Cache response."""
        # Don't cache error responses or responses with missing parameters
        if response.intent not in ["error"] and response.answer and not response.answer.startswith("To complete your query"):
            # Clean up old cache entries (simple LRU-like behavior)
            if len(self._response_cache) > 100:  # Limit cache size
                oldest_key = min(self._response_cache.keys(), 
                               key=lambda k: self._response_cache[k][1])
                del self._response_cache[oldest_key]
            
            self._response_cache[query_hash] = (response, time.time())
            logger.info("Cached response", query_hash=query_hash)
    
    def clear_response_cache(self):
        """Clear the response cache - useful for testing and debugging."""
        cache_size = len(self._response_cache)
        self._response_cache.clear()
        logger.info("Response cache cleared", previous_size=cache_size)