from typing import Dict, List, Any

class CypherTemplate:
    def __init__(self, query: str, required_params: List[str], description: str):
        self.query = query
        self.required_params = required_params
        self.description = description
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Return list of missing required parameters."""
        return [param for param in self.required_params if param not in params]
    
    def has_limit(self) -> bool:
        """Check if query has LIMIT clause for security."""
        return "LIMIT" in self.query.upper()
    
    def is_read_only(self) -> bool:
        """Check if query is read-only (no write operations)."""
        write_operations = ["CREATE", "DELETE", "SET", "MERGE", "DROP", "REMOVE"]
        query_upper = self.query.upper()
        return not any(op in query_upper for op in write_operations)

CYPHER_TEMPLATES = {
    "etf_exposure_to_company": CypherTemplate(
        query="""
            MATCH (e:ETF {ticker: $ticker})-[h:HOLDS]->(c:Company {symbol: $symbol})
            RETURN e.ticker as etf_ticker, e.name as etf_name,
                   c.symbol, c.name as company_name, 
                   round(h.weight * 100, 3) as exposure_percent
            ORDER BY h.weight DESC
            LIMIT 50
        """,
        required_params=["ticker", "symbol"],
        description="Find ETF exposure to specific company"
    ),
    
    "etf_overlap_weighted": CypherTemplate(
        query="""
            MATCH (e1:ETF {ticker: $ticker1})-[h1:HOLDS]->(c:Company)<-[h2:HOLDS]-(e2:ETF {ticker: $ticker2})
            RETURN c.symbol, c.name as company_name, 
                   round(h1.weight * 100, 3) as percent_etf1,
                   round(h2.weight * 100, 3) as percent_etf2,
                   round((h1.weight + h2.weight) * 100, 3) as combined_percent,
                   round(abs(h1.weight - h2.weight) * 100, 3) as difference_percent
            ORDER BY (h1.weight + h2.weight) DESC
            LIMIT 50
        """,
        required_params=["ticker1", "ticker2"],
        description="Calculate weighted overlap between two ETFs"
    ),
    
    "etf_overlap_jaccard": CypherTemplate(
        query="""
            MATCH (e1:ETF {ticker: $ticker1})-[:HOLDS]->(c:Company)<-[:HOLDS]-(e2:ETF {ticker: $ticker2})
            WITH count(c) as intersection
            MATCH (e1:ETF {ticker: $ticker1})-[:HOLDS]->(c1:Company)
            WITH intersection, count(c1) as count1
            MATCH (e2:ETF {ticker: $ticker2})-[:HOLDS]->(c2:Company)  
            WITH intersection, count1, count(c2) as count2
            RETURN intersection, count1, count2, 
                   toFloat(intersection) / (count1 + count2 - intersection) as jaccard_similarity,
                   toFloat(intersection) / count1 as overlap_ratio_etf1,
                   toFloat(intersection) / count2 as overlap_ratio_etf2,
                   round(toFloat(intersection) / (count1 + count2 - intersection) * 100, 2) as jaccard_percent
            LIMIT 1
        """,
        required_params=["ticker1", "ticker2"],
        description="Calculate Jaccard overlap coefficient between ETFs"
    ),
    
    "sector_exposure": CypherTemplate(
        query="""
            MATCH (e:ETF {ticker: $ticker})-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
            WITH s.name as sector, 
                 count(c) as company_count,
                 sum(h.weight) as total_weight,
                 avg(h.weight) as avg_weight,
                 max(h.weight) as max_weight
            RETURN sector, 
                   company_count,
                   round(total_weight * 100, 2) as exposure_percent,
                   round(avg_weight * 100, 3) as avg_exposure_percent,
                   round(max_weight * 100, 3) as max_exposure_percent
            ORDER BY total_weight DESC
            LIMIT 50
        """,
        required_params=["ticker"],
        description="Show sector distribution for ETF"
    ),
    
    "etfs_by_sector_threshold": CypherTemplate(
        query="""
            // Optimized query: start from sector to use index efficiently
            MATCH (s:Sector)
            WHERE s.name = $sector OR s.name CONTAINS $sector
            WITH s
            MATCH (s)<-[:IN_SECTOR]-(c:Company)<-[h:HOLDS]-(e:ETF)
            WITH e, sum(h.weight) as sector_exposure
            WHERE sector_exposure >= $threshold
            RETURN e.ticker, e.name as etf_name,
                   round(sector_exposure * 100, 2) as exposure_percent
            ORDER BY sector_exposure DESC
            LIMIT 50
        """,
        required_params=["sector", "threshold"],
        description="Find ETFs with minimum sector exposure"
    ),
    
    "top_holdings_subgraph": CypherTemplate(
        query="""
            MATCH (e:ETF {ticker: $ticker})-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
            RETURN c.symbol, c.name as company_name, s.name as sector,
                   round(h.weight * 100, 3) as exposure_percent
            ORDER BY h.weight DESC
            LIMIT $top_n
        """,
        required_params=["ticker", "top_n"],
        description="Get top holdings with weights and sectors"
    ),
    
    "company_rankings": CypherTemplate(
        query="""
            MATCH (c:Company {symbol: $symbol})<-[h:HOLDS]-(e:ETF)
            WHERE ($etf_tickers IS NULL OR e.ticker IN $etf_tickers)
            RETURN e.ticker, e.name as etf_name, 
                   round(h.weight * 100, 3) as exposure_percent
            ORDER BY h.weight DESC
            LIMIT 50
        """,
        required_params=["symbol"],
        description="Rank ETFs by exposure to specific company (optionally filtered by ETF list)"
    ),
    
    "general_llm": CypherTemplate(
        query="",  # No Cypher query needed
        required_params=[],
        description="Handle general questions with LLM knowledge"
    ),
    
    "comprehensive_data": CypherTemplate(
        query="""
            // Get all ETF holdings with comprehensive data
            MATCH (e:ETF)-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
            WITH e, c, s, h 
            ORDER BY e.ticker, h.weight DESC
            WITH e, 
                 collect({
                     symbol: c.symbol,
                     name: c.name,
                     sector: s.name,
                     weight: h.weight,
                     shares: h.shares,
                     exposure_percent: round(h.weight * 100, 3)
                 })[0..50] as holdings,
                 count(c) as total_holdings,
                 sum(h.weight) as total_weight
            
            // Get sector distributions
            MATCH (e)-[h2:HOLDS]->(c2:Company)-[:IN_SECTOR]->(s2:Sector)
            WITH e, holdings, total_holdings, total_weight,
                 s2.name as sector,
                 sum(h2.weight) as sector_weight,
                 count(c2) as sector_count
            WITH e, holdings, total_holdings, total_weight,
                 collect({
                     sector: sector,
                     weight: round(sector_weight * 100, 2),
                     count: sector_count
                 }) as sectors
            
            RETURN e.ticker as etf_ticker, 
                   e.name as etf_name,
                   total_holdings,
                   holdings,
                   sectors
            ORDER BY e.ticker
            LIMIT 10
        """,
        required_params=[],
        description="Get comprehensive ETF holdings and sector data for all ETFs"
    )
}

def get_template(intent_key: str) -> CypherTemplate:
    """Get Cypher template by intent key."""
    if intent_key not in CYPHER_TEMPLATES:
        raise ValueError(f"Unknown intent: {intent_key}")
    return CYPHER_TEMPLATES[intent_key]

def list_available_intents() -> List[str]:
    """List all available intent keys."""
    return list(CYPHER_TEMPLATES.keys())

def validate_all_templates() -> Dict[str, Dict[str, bool]]:
    """Validate all templates for security requirements."""
    validation_results = {}
    
    for intent_key, template in CYPHER_TEMPLATES.items():
        validation_results[intent_key] = {
            "has_limit": template.has_limit(),
            "is_read_only": template.is_read_only(),
            "has_required_params": len(template.required_params) > 0
        }
    
    return validation_results