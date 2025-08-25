#!/usr/bin/env python3
"""
System initialization script for ETF GraphRAG platform.
Initializes Neo4j schema, seeds GraphRAG data, and loads real ETF holdings.
"""

import asyncio
import os
import logging
import time
import json
from neo4j import AsyncGraphDatabase
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemInitializer:
    def __init__(self):
        self.neo4j_driver = None
        self.api_base_url = "http://api:8000"
        
    async def initialize(self):
        """Run complete system initialization."""
        logger.info("🚀 Starting ETF GraphRAG system initialization...")
        
        try:
            logger.info("Step 1/6: Setting up Neo4j connection...")
            await self.setup_neo4j()
            
            logger.info("Step 2/6: Setting up Neo4j schema...")
            await self.setup_schema()
            
            logger.info("Step 3/6: Seeding GraphRAG data...")
            await self.seed_data()
            
            logger.info("Step 4/6: Waiting for API service...")
            await self.wait_for_api()
            
            logger.info("Step 5/6: Loading real ETF holdings data...")
            await self.load_real_etf_data()
            
            logger.info("Step 6/6: Validating system...")
            await self.validate_system()
            
            logger.info("✅ System initialization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {str(e)}")
            logger.exception("Full error details:")
            return False
        finally:
            await self.cleanup()
    
    async def setup_neo4j(self):
        """Initialize Neo4j connection."""
        
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password123')
        
        # Wait for Neo4j to be ready
        max_retries = 30
        for attempt in range(max_retries):
            try:
                self.neo4j_driver = AsyncGraphDatabase.driver(
                    neo4j_uri, auth=(neo4j_user, neo4j_password)
                )
                
                # Test connection
                async with self.neo4j_driver.session() as session:
                    result = await session.run("RETURN 1 as health")
                    await result.single()
                    
                logger.info("✅ Neo4j connection established")
                break
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to connect to Neo4j after {max_retries} attempts: {str(e)}")
                logger.info(f"⏳ Waiting for Neo4j... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)
    
    async def setup_schema(self):
        """Create Neo4j schema, constraints, and indexes."""
        
        schema_commands = [
            # Unique constraints
            "CREATE CONSTRAINT etf_ticker_unique IF NOT EXISTS FOR (e:ETF) REQUIRE e.ticker IS UNIQUE",
            "CREATE CONSTRAINT company_symbol_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.symbol IS UNIQUE", 
            "CREATE CONSTRAINT sector_name_unique IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT intent_key_unique IF NOT EXISTS FOR (i:Intent) REQUIRE i.key IS UNIQUE",
            "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX term_norm_index IF NOT EXISTS FOR (t:Term) ON (t.norm)",
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX holds_weight_index IF NOT EXISTS FOR ()-[h:HOLDS]-() ON (h.weight)",
        ]
        
        async with self.neo4j_driver.session() as session:
            for command in schema_commands:
                try:
                    await session.run(command)
                    logger.info(f"✅ Executed: {command[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️  Schema command failed: {str(e)}")
    
    async def seed_data(self):
        """Seed initial GraphRAG data."""
        
        async with self.neo4j_driver.session() as session:
            # Create intents
            intents = [
                {
                    'key': 'etf_exposure_to_company',
                    'description': 'Find ETF exposure to specific company',
                    'confidence_threshold': 0.7,
                    'required_entities': ['ETF', 'Company']
                },
                {
                    'key': 'etf_overlap_weighted',
                    'description': 'Calculate weighted overlap between ETFs',
                    'confidence_threshold': 0.8,
                    'required_entities': ['ETF', 'ETF']
                },
                {
                    'key': 'sector_exposure',
                    'description': 'Show sector distribution for ETF',
                    'confidence_threshold': 0.7,
                    'required_entities': ['ETF']
                },
                {
                    'key': 'top_holdings_subgraph',
                    'description': 'Get top holdings for graph visualization',
                    'confidence_threshold': 0.6,
                    'required_entities': ['ETF', 'Count']
                }
            ]
            
            for intent_data in intents:
                await session.run(
                    """
                    MERGE (i:Intent {key: $key})
                    SET i.description = $description,
                        i.confidence_threshold = $confidence_threshold,
                        i.required_entities = $required_entities,
                        i.created_at = datetime()
                    """,
                    intent_data
                )
            
            logger.info(f"✅ Created {len(intents)} intents")
            
            # Create ETF entities
            etf_entities = [
                {'name': 'SPY', 'type': 'ETF', 'description': 'SPDR S&P 500 ETF'},
                {'name': 'QQQ', 'type': 'ETF', 'description': 'Invesco QQQ Trust'},
                {'name': 'IWM', 'type': 'ETF', 'description': 'iShares Russell 2000 ETF'},
                {'name': 'IJH', 'type': 'ETF', 'description': 'iShares Core S&P Mid-Cap ETF'},
                {'name': 'IVE', 'type': 'ETF', 'description': 'iShares S&P 500 Value ETF'},
                {'name': 'IVW', 'type': 'ETF', 'description': 'iShares S&P 500 Growth ETF'}
            ]
            
            for entity_data in etf_entities:
                await session.run(
                    """
                    MERGE (e:Entity {name: $name, type: $type})
                    SET e.description = $description,
                        e.created_at = datetime()
                    """,
                    entity_data
                )
            
            logger.info(f"✅ Created {len(etf_entities)} ETF entities")
            
            # Create sector entities
            sector_entities = [
                {'name': 'Technology', 'type': 'Sector'},
                {'name': 'Healthcare', 'type': 'Sector'},
                {'name': 'Financials', 'type': 'Sector'},
                {'name': 'Consumer Discretionary', 'type': 'Sector'},
                {'name': 'Communication Services', 'type': 'Sector'},
                {'name': 'Industrials', 'type': 'Sector'}
            ]
            
            for entity_data in sector_entities:
                await session.run(
                    """
                    MERGE (e:Entity {name: $name, type: $type})
                    SET e.created_at = datetime()
                    """,
                    entity_data
                )
            
            logger.info(f"✅ Created {len(sector_entities)} sector entities")
    
    async def wait_for_api(self):
        """Wait for the API service to be ready."""
        
        max_retries = 60  # Wait up to 10 minutes
        retry_interval = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.api_base_url}/health")
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get("status") == "healthy":
                            logger.info("✅ API service is healthy and ready")
                            return
                        else:
                            logger.info(f"⏳ API not fully healthy yet: {health_data}")
                            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"API service not ready after {max_retries * retry_interval} seconds: {str(e)}")
                logger.info(f"⏳ API not ready yet (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
            await asyncio.sleep(retry_interval)
    
    async def load_real_etf_data(self):
        """Load real ETF holdings data via the API."""
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for ETL
                logger.info("🔄 Calling ETL refresh endpoint to load real data...")
                response = await client.post(f"{self.api_base_url}/etl/refresh/force")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ ETL refresh completed successfully")
                    logger.info(f"   - Processed ETFs: {result.get('tickers_processed', [])}")
                    logger.info(f"   - Success: {result.get('success', False)}")
                    logger.info(f"   - Message: {result.get('message', 'No message')}")
                    
                    if not result.get('success', False):
                        logger.warning("⚠️ ETL refresh reported non-success status but completed")
                        
                else:
                    logger.error(f"❌ ETL refresh failed with status {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    raise Exception(f"ETL refresh API returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to load real ETF data: {str(e)}")
            raise
    
    async def validate_system(self):
        """Validate that all system components are working correctly."""
        
        async with self.neo4j_driver.session() as session:
            # Check intents
            result = await session.run("MATCH (i:Intent) RETURN count(i) as count")
            intent_count = (await result.single())['count']
            logger.info(f"✅ Found {intent_count} intents in database")
            
            # Check entities
            result = await session.run("MATCH (e:Entity) RETURN count(e) as count")
            entity_count = (await result.single())['count']
            logger.info(f"✅ Found {entity_count} entities in database")
            
            # Check ETFs
            result = await session.run("MATCH (e:ETF) RETURN count(e) as count")
            etf_count = (await result.single())['count']
            logger.info(f"✅ Found {etf_count} ETFs in database")
            
            # Check companies (real holdings data)
            result = await session.run("MATCH (c:Company) RETURN count(c) as count")
            company_count = (await result.single())['count']
            logger.info(f"✅ Found {company_count} companies in database")
            
            # Check holdings relationships
            result = await session.run("MATCH ()-[h:HOLDS]->() RETURN count(h) as count")
            holdings_count = (await result.single())['count']
            logger.info(f"✅ Found {holdings_count} holdings relationships")
            
            if company_count > 0 and holdings_count > 0:
                logger.info("✅ Real ETF data successfully loaded!")
            else:
                logger.warning("⚠️ No real ETF data found - ETL may have failed")
        
        logger.info("✅ System validation completed")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.neo4j_driver:
            await self.neo4j_driver.close()

async def main():
    """Main initialization function."""
    initializer = SystemInitializer()
    success = await initializer.initialize()
    
    if success:
        logger.info("🎉 ETF GraphRAG system is ready to use!")
        return 0
    else:
        logger.error("💥 System initialization failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))