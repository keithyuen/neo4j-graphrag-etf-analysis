import structlog
from typing import List, Dict, Any, Optional
from app.models.entities import GroundedEntity, EntityType, PreprocessedText
from app.services.neo4j_service import Neo4jService

logger = structlog.get_logger()

class EntityGrounder:
    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j = neo4j_service
        
    async def ground_entities(self, preprocessed: PreprocessedText) -> List[GroundedEntity]:
        """
        Ground entities from preprocessed text.
        Returns list of grounded entities with confidence scores.
        """
        entities = []
        
        # Ground ticker symbols as ETFs first
        etf_entities = await self._ground_etfs(preprocessed.potential_tickers)
        entities.extend(etf_entities)
        
        # Ground remaining tickers as companies (exclude those found as ETFs)
        etf_tickers = {entity.name for entity in etf_entities}
        company_tickers = [t for t in preprocessed.potential_tickers if t not in etf_tickers]
        company_entities = await self._ground_companies(company_tickers)
        entities.extend(company_entities)
        
        # Ground sectors from tokens
        sector_entities = await self._ground_sectors(preprocessed.tokens)
        entities.extend(sector_entities)
        
        # Ground numerical entities
        number_entities = self._ground_numbers(preprocessed.extracted_numbers)
        entities.extend(number_entities)
        
        logger.info("Entity grounding completed", 
                   total_entities=len(entities),
                   etfs=len(etf_entities),
                   companies=len(company_entities),
                   sectors=len(sector_entities),
                   numbers=len(number_entities))
        
        return entities
    
    async def _ground_etfs(self, potential_tickers: List[str]) -> List[GroundedEntity]:
        """Ground ETF ticker symbols."""
        entities = []
        
        for ticker in potential_tickers:
            query = "MATCH (e:ETF {ticker: $ticker}) RETURN e"
            result = await self.neo4j.execute_query_single(query, {"ticker": ticker})
            
            if result:
                entities.append(GroundedEntity(
                    name=ticker,
                    type=EntityType.ETF,
                    confidence=1.0,
                    properties=result['e']
                ))
                logger.debug("ETF grounded", ticker=ticker)
        
        return entities
    
    async def _ground_companies(self, potential_tickers: List[str]) -> List[GroundedEntity]:
        """Ground company symbols."""
        entities = []
        
        for symbol in potential_tickers:
            query = "MATCH (c:Company {symbol: $symbol}) RETURN c"
            result = await self.neo4j.execute_query_single(query, {"symbol": symbol})
            
            if result:
                entities.append(GroundedEntity(
                    name=symbol,
                    type=EntityType.COMPANY,
                    confidence=1.0,
                    properties=result['c']
                ))
                logger.debug("Company grounded", symbol=symbol)
        
        return entities
    
    async def _ground_sectors(self, tokens: List[str]) -> List[GroundedEntity]:
        """Ground sector names and aliases."""
        entities = []
        
        # Direct sector matching
        for token in tokens:
            # Skip very short tokens
            if len(token) < 3:
                continue
                
            query = "MATCH (s:Sector) WHERE toLower(s.name) = $token RETURN s"
            results = await self.neo4j.execute_query(query, {"token": token})
            
            for result in results:
                entities.append(GroundedEntity(
                    name=result['s']['name'],
                    type=EntityType.SECTOR,
                    confidence=0.8,  # Lower confidence for partial matches
                    properties=result['s']
                ))
                logger.debug("Sector grounded via direct match", token=token, sector=result['s']['name'])
        
        # Term alias matching
        for token in tokens:
            if len(token) < 3:
                continue
                
            query = """
                MATCH (t:Term {norm: $token})-[:ALIAS_OF]->(e:Entity)-[:REFERS_TO]->(s:Sector)
                RETURN s, e
            """
            results = await self.neo4j.execute_query(query, {"token": token})
            
            for result in results:
                entities.append(GroundedEntity(
                    name=result['s']['name'],
                    type=EntityType.SECTOR,
                    confidence=0.9,  # Higher confidence for explicit aliases
                    properties=result['s']
                ))
                logger.debug("Sector grounded via alias", token=token, sector=result['s']['name'])
        
        # Remove duplicates by name
        seen_sectors = set()
        unique_entities = []
        for entity in entities:
            if entity.type == EntityType.SECTOR and entity.name not in seen_sectors:
                seen_sectors.add(entity.name)
                unique_entities.append(entity)
            elif entity.type != EntityType.SECTOR:
                unique_entities.append(entity)
        
        return unique_entities
    
    def _ground_numbers(self, numbers: Dict[str, List[float]]) -> List[GroundedEntity]:
        """Ground numerical entities."""
        entities = []
        
        # Ground percentages and thresholds
        for percentage in numbers.get('percentages', []) + numbers.get('thresholds', []):
            entities.append(GroundedEntity(
                name=f"{percentage:.1%}",
                type=EntityType.PERCENT,
                confidence=1.0,
                properties={"value": percentage}
            ))
        
        # Ground counts
        for count in numbers.get('counts', []):
            entities.append(GroundedEntity(
                name=str(count),
                type=EntityType.COUNT,
                confidence=1.0,
                properties={"value": count}
            ))
        
        return entities