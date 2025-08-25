#!/usr/bin/env python3
"""
Load sample ETF data into Neo4j for testing.
Creates realistic sample data for the GraphRAG system.
"""

import asyncio
import logging
from neo4j import AsyncGraphDatabase
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_sample_data():
    """Load sample ETF holdings data into Neo4j."""
    
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password123')
    
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        async with driver.session() as session:
            logger.info("🚀 Loading sample ETF data...")
            
            # Sample ETF data with realistic holdings
            sample_data = [
                # SPY Holdings (S&P 500)
                {"etf": "SPY", "company": "AAPL", "name": "Apple Inc", "sector": "Technology", "weight": 0.0734, "shares": 156800000},
                {"etf": "SPY", "company": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "weight": 0.0681, "shares": 71200000},
                {"etf": "SPY", "company": "GOOGL", "name": "Alphabet Inc Class A", "sector": "Communication Services", "weight": 0.0418, "shares": 13500000},
                {"etf": "SPY", "company": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Discretionary", "weight": 0.0354, "shares": 21800000},
                {"etf": "SPY", "company": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "weight": 0.0285, "shares": 11900000},
                {"etf": "SPY", "company": "TSLA", "name": "Tesla Inc", "sector": "Consumer Discretionary", "weight": 0.0235, "shares": 23400000},
                {"etf": "SPY", "company": "META", "name": "Meta Platforms Inc", "sector": "Communication Services", "weight": 0.0225, "shares": 12100000},
                {"etf": "SPY", "company": "BRK.B", "name": "Berkshire Hathaway Inc Class B", "sector": "Financials", "weight": 0.0168, "shares": 12800000},
                {"etf": "SPY", "company": "UNH", "name": "UnitedHealth Group Inc", "sector": "Healthcare", "weight": 0.0135, "shares": 8900000},
                {"etf": "SPY", "company": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "weight": 0.0125, "shares": 19200000},
                
                # QQQ Holdings (Nasdaq 100)
                {"etf": "QQQ", "company": "AAPL", "name": "Apple Inc", "sector": "Technology", "weight": 0.0891, "shares": 41200000},
                {"etf": "QQQ", "company": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "weight": 0.0825, "shares": 18700000},
                {"etf": "QQQ", "company": "GOOGL", "name": "Alphabet Inc Class A", "sector": "Communication Services", "weight": 0.0506, "shares": 3540000},
                {"etf": "QQQ", "company": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Discretionary", "weight": 0.0429, "shares": 5730000},
                {"etf": "QQQ", "company": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "weight": 0.0346, "shares": 3120000},
                {"etf": "QQQ", "company": "META", "name": "Meta Platforms Inc", "sector": "Communication Services", "weight": 0.0273, "shares": 3180000},
                {"etf": "QQQ", "company": "TSLA", "name": "Tesla Inc", "sector": "Consumer Discretionary", "weight": 0.0285, "shares": 6150000},
                {"etf": "QQQ", "company": "AVGO", "name": "Broadcom Inc", "sector": "Technology", "weight": 0.0178, "shares": 1870000},
                {"etf": "QQQ", "company": "COST", "name": "Costco Wholesale Corporation", "sector": "Consumer Staples", "weight": 0.0165, "shares": 2450000},
                {"etf": "QQQ", "company": "NFLX", "name": "Netflix Inc", "sector": "Communication Services", "weight": 0.0142, "shares": 3210000},
                
                # IWM Holdings (Russell 2000 - Small Cap)
                {"etf": "IWM", "company": "SMCI", "name": "Super Micro Computer Inc", "sector": "Technology", "weight": 0.0084, "shares": 950000},
                {"etf": "IWM", "company": "KVUE", "name": "Kenvue Inc", "sector": "Healthcare", "weight": 0.0071, "shares": 8900000},
                {"etf": "IWM", "company": "SOLV", "name": "Solventum Corporation", "sector": "Healthcare", "weight": 0.0068, "shares": 2100000},
                {"etf": "IWM", "company": "TPG", "name": "Texas Pacific Land Corporation", "sector": "Energy", "weight": 0.0065, "shares": 1200000},
                {"etf": "IWM", "company": "RKLB", "name": "Rocket Lab USA Inc", "sector": "Industrials", "weight": 0.0058, "shares": 4200000},
                {"etf": "IWM", "company": "DOCN", "name": "DigitalOcean Holdings Inc", "sector": "Technology", "weight": 0.0052, "shares": 2800000},
                {"etf": "IWM", "company": "RYAN", "name": "Ryan Specialty Holdings Inc", "sector": "Financials", "weight": 0.0048, "shares": 2100000},
                
                # IJH Holdings (S&P Mid-Cap 400)
                {"etf": "IJH", "company": "SMCI", "name": "Super Micro Computer Inc", "sector": "Technology", "weight": 0.0156, "shares": 1780000},
                {"etf": "IJH", "company": "TPG", "name": "Texas Pacific Land Corporation", "sector": "Energy", "weight": 0.0142, "shares": 2600000},
                {"etf": "IJH", "company": "COIN", "name": "Coinbase Global Inc", "sector": "Technology", "weight": 0.0135, "shares": 1890000},
                {"etf": "IJH", "company": "GDDY", "name": "GoDaddy Inc", "sector": "Technology", "weight": 0.0128, "shares": 3450000},
                {"etf": "IJH", "company": "DECK", "name": "Deckers Outdoor Corporation", "sector": "Consumer Discretionary", "weight": 0.0118, "shares": 890000},
                
                # IVE Holdings (S&P 500 Value)
                {"etf": "IVE", "company": "BRK.B", "name": "Berkshire Hathaway Inc Class B", "sector": "Financials", "weight": 0.0398, "shares": 30200000},
                {"etf": "IVE", "company": "JPM", "name": "JPMorgan Chase & Co", "sector": "Financials", "weight": 0.0312, "shares": 28900000},
                {"etf": "IVE", "company": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy", "weight": 0.0285, "shares": 61200000},
                {"etf": "IVE", "company": "UNH", "name": "UnitedHealth Group Inc", "sector": "Healthcare", "weight": 0.0265, "shares": 17800000},
                {"etf": "IVE", "company": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "weight": 0.0235, "shares": 36100000},
                
                # IVW Holdings (S&P 500 Growth)
                {"etf": "IVW", "company": "AAPL", "name": "Apple Inc", "sector": "Technology", "weight": 0.1248, "shares": 267000000},
                {"etf": "IVW", "company": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "weight": 0.1156, "shares": 121000000},
                {"etf": "IVW", "company": "GOOGL", "name": "Alphabet Inc Class A", "sector": "Communication Services", "weight": 0.0710, "shares": 22900000},
                {"etf": "IVW", "company": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Discretionary", "weight": 0.0601, "shares": 37000000},
                {"etf": "IVW", "company": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "weight": 0.0484, "shares": 20200000},
            ]
            
            # Create ETFs
            etfs = [
                {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust", "description": "Tracks the S&P 500 Index"},
                {"ticker": "QQQ", "name": "Invesco QQQ Trust", "description": "Tracks the Nasdaq-100 Index"},
                {"ticker": "IWM", "name": "iShares Russell 2000 ETF", "description": "Tracks the Russell 2000 Index"},
                {"ticker": "IJH", "name": "iShares Core S&P Mid-Cap ETF", "description": "Tracks the S&P MidCap 400 Index"},
                {"ticker": "IVE", "name": "iShares S&P 500 Value ETF", "description": "Tracks the S&P 500 Value Index"},
                {"ticker": "IVW", "name": "iShares S&P 500 Growth ETF", "description": "Tracks the S&P 500 Growth Index"}
            ]
            
            for etf in etfs:
                await session.run("""
                    MERGE (e:ETF {ticker: $ticker})
                    SET e.name = $name,
                        e.description = $description,
                        e.created_at = datetime(),
                        e.updated_at = datetime()
                """, etf)
            
            logger.info(f"✅ Created {len(etfs)} ETFs")
            
            # Get unique sectors
            sectors = list(set(holding["sector"] for holding in sample_data))
            
            for sector_name in sectors:
                await session.run("""
                    MERGE (s:Sector {name: $name})
                    SET s.created_at = datetime(),
                        s.updated_at = datetime()
                """, {"name": sector_name})
            
            logger.info(f"✅ Created {len(sectors)} sectors")
            
            # Create holdings data
            for holding in sample_data:
                await session.run("""
                    // Create or update company
                    MERGE (c:Company {symbol: $symbol})
                    SET c.name = $name,
                        c.created_at = CASE WHEN c.created_at IS NULL THEN datetime() ELSE c.created_at END,
                        c.updated_at = datetime()
                    
                    // Connect company to sector
                    WITH c
                    MATCH (s:Sector {name: $sector})
                    MERGE (c)-[:IN_SECTOR]->(s)
                    
                    // Connect ETF to company with holdings relationship
                    WITH c
                    MATCH (e:ETF {ticker: $etf})
                    MERGE (e)-[h:HOLDS]->(c)
                    SET h.weight = $weight,
                        h.shares = $shares,
                        h.updated_at = datetime()
                """, {
                    "etf": holding["etf"],
                    "symbol": holding["company"], 
                    "name": holding["name"],
                    "sector": holding["sector"],
                    "weight": holding["weight"],
                    "shares": holding["shares"]
                })
            
            logger.info(f"✅ Created {len(sample_data)} holdings relationships")
            
            # Verify data
            result = await session.run("""
                MATCH (e:ETF)-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
                RETURN e.ticker as etf, count(c) as holdings_count
                ORDER BY e.ticker
            """)
            
            holdings_summary = []
            async for record in result:
                holdings_summary.append(f"{record['etf']}: {record['holdings_count']} holdings")
            
            logger.info("📊 Holdings summary:")
            for summary in holdings_summary:
                logger.info(f"   {summary}")
            
            # Create some additional companies that can be queried
            additional_companies = [
                {"symbol": "GOOG", "name": "Alphabet Inc Class C", "sector": "Communication Services"},
                {"symbol": "WMT", "name": "Walmart Inc", "sector": "Consumer Staples"},
                {"symbol": "V", "name": "Visa Inc", "sector": "Financials"},
                {"symbol": "HD", "name": "The Home Depot Inc", "sector": "Consumer Discretionary"},
                {"symbol": "PG", "name": "The Procter & Gamble Company", "sector": "Consumer Staples"},
            ]
            
            for company in additional_companies:
                await session.run("""
                    MERGE (c:Company {symbol: $symbol})
                    SET c.name = $name,
                        c.created_at = CASE WHEN c.created_at IS NULL THEN datetime() ELSE c.created_at END,
                        c.updated_at = datetime()
                    WITH c
                    MATCH (s:Sector {name: $sector})
                    MERGE (c)-[:IN_SECTOR]->(s)
                """, company)
            
            logger.info(f"✅ Added {len(additional_companies)} additional companies")
            
            logger.info("🎉 Sample data loading completed successfully!")
            
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(load_sample_data())