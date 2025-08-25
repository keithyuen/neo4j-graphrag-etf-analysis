import structlog
from typing import List, Dict, Any
from app.models.entities import GroundedEntity, IntentResult, ParameterFulfillment, EntityType

logger = structlog.get_logger()

class ParameterFulfiller:
    def __init__(self, neo4j_service):
        self.neo4j = neo4j_service
    
    async def fulfill(self, intent_result: IntentResult, entities: List[GroundedEntity]) -> ParameterFulfillment:
        """
        Fulfill parameters required for the classified intent using grounded entities.
        Returns ParameterFulfillment with extracted parameters and missing ones.
        """
        parameters = {}
        missing_parameters = []
        
        # Extract parameters based on intent type
        if intent_result.intent == "etf_exposure_to_company":
            ticker = self._find_entity_value(entities, EntityType.ETF)
            symbol = self._find_entity_value(entities, EntityType.COMPANY)
            
            if ticker:
                parameters["ticker"] = ticker
            else:
                missing_parameters.append("ticker")
                
            if symbol:
                parameters["symbol"] = symbol
            else:
                missing_parameters.append("symbol")
        
        elif intent_result.intent in ["etf_overlap_weighted", "etf_overlap_jaccard"]:
            etf_entities = [e for e in entities if e.type == EntityType.ETF]
            
            if len(etf_entities) >= 2:
                parameters["ticker1"] = etf_entities[0].name
                parameters["ticker2"] = etf_entities[1].name
            elif len(etf_entities) == 1:
                parameters["ticker1"] = etf_entities[0].name
                missing_parameters.append("ticker2")
            else:
                missing_parameters.extend(["ticker1", "ticker2"])
        
        elif intent_result.intent == "sector_exposure":
            ticker = self._find_entity_value(entities, EntityType.ETF)
            
            if ticker:
                parameters["ticker"] = ticker
            else:
                missing_parameters.append("ticker")
        
        elif intent_result.intent == "etfs_by_sector_threshold":
            sector = self._find_entity_value(entities, EntityType.SECTOR)
            threshold = self._find_entity_value(entities, EntityType.PERCENT)
            
            if sector:
                parameters["sector"] = sector
            else:
                missing_parameters.append("sector")
                
            if threshold is not None:
                parameters["threshold"] = threshold
            else:
                # Default threshold if not specified
                parameters["threshold"] = 0.05  # 5%
        
        elif intent_result.intent == "top_holdings_subgraph":
            ticker = self._find_entity_value(entities, EntityType.ETF)
            top_n = self._find_entity_value(entities, EntityType.COUNT)
            
            if ticker:
                parameters["ticker"] = ticker
            else:
                missing_parameters.append("ticker")
                
            if top_n is not None:
                parameters["top_n"] = min(int(top_n), 50)  # Cap at 50 for security
            else:
                parameters["top_n"] = 10  # Default
        
        elif intent_result.intent == "company_rankings":
            symbol = self._find_entity_value(entities, EntityType.COMPANY)
            etf_tickers = self._find_all_entity_values(entities, EntityType.ETF)
            
            if symbol:
                parameters["symbol"] = symbol
            else:
                missing_parameters.append("symbol")
                
            # Add ETF filter if specific ETFs are mentioned
            if etf_tickers:
                parameters["etf_tickers"] = etf_tickers
            else:
                parameters["etf_tickers"] = None
                
        elif intent_result.intent == "general_llm":
            # No parameters needed for general LLM responses
            pass
        
        # Validate all required parameters are present
        is_complete = len(missing_parameters) == 0
        
        result = ParameterFulfillment(
            parameters=parameters,
            missing_parameters=missing_parameters,
            is_complete=is_complete
        )
        
        logger.info("Parameter fulfillment completed",
                   intent=intent_result.intent,
                   parameters_found=len(parameters),
                   missing_count=len(missing_parameters),
                   is_complete=is_complete)
        
        return result
    
    def _find_entity_value(self, entities: List[GroundedEntity], entity_type: EntityType) -> Any:
        """Find the best entity of the specified type and return its value."""
        candidates = [entity for entity in entities if entity.type == entity_type]
        if not candidates:
            return None
            
        # Select the best candidate based on confidence and specificity
        best_entity = max(candidates, key=lambda e: (
            e.confidence,  # Higher confidence first
            len(e.name)    # Longer names are more specific (e.g., "Information Technology" vs "Technology")
        ))
        
        if entity_type in [EntityType.PERCENT, EntityType.COUNT]:
            # Return the actual numeric value
            return best_entity.properties.get("value", best_entity.name)
        else:
            # Return the name for tickers, symbols, sectors
            return best_entity.name
    
    def _find_all_entity_values(self, entities: List[GroundedEntity], entity_type: EntityType) -> List[Any]:
        """Find all entities of the specified type and return their values."""
        values = []
        for entity in entities:
            if entity.type == entity_type:
                if entity_type in [EntityType.PERCENT, EntityType.COUNT]:
                    values.append(entity.properties.get("value", entity.name))
                else:
                    values.append(entity.name)
        return values