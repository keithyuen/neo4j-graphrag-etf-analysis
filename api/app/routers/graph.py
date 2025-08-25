from fastapi import APIRouter, HTTPException, Query
import structlog
from typing import Optional
from app.models.responses import SubgraphResponse, GraphNode, GraphEdge, ResponseMetadata
from app.utils.validators import validate_subgraph_params
from app.utils.security import security
from app.services.neo4j_service import Neo4jService
import time

logger = structlog.get_logger()
router = APIRouter()

# Global service instance
neo4j_service = None

@router.get("/subgraph", response_model=SubgraphResponse)
async def get_subgraph(
    ticker: str = Query(..., description="ETF ticker symbol"),
    top: int = Query(default=10, ge=1, le=50, description="Number of top holdings"),
    edge_weight_threshold: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum edge weight")
):
    """
    Get subgraph data for Cytoscape visualization.
    Returns nodes (ETF, Company, Sector) and edges (HOLDS, IN_SECTOR) for the top holdings of an ETF.
    
    This endpoint provides data specifically formatted for Cytoscape.js:
    - Nodes with unique IDs, labels, types, and properties
    - Edges with source/target references and properties
    - Filtered by edge weight threshold
    - Limited to top N holdings for performance
    """
    if neo4j_service is None:
        raise HTTPException(status_code=503, detail="Neo4j service not initialized")
    
    start_time = time.time()
    
    try:
        # Validate parameters
        params = validate_subgraph_params(ticker, top, edge_weight_threshold)
        
        logger.info("Processing subgraph request",
                   ticker=params['ticker'],
                   top_n=params['top_n'],
                   threshold=params['edge_weight_threshold'])
        
        # Execute subgraph query
        query = """
            MATCH (e:ETF {ticker: $ticker})-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
            WHERE h.weight >= $threshold
            RETURN e, h, c, s
            ORDER BY h.weight DESC
            LIMIT $top_n
        """
        
        results = await neo4j_service.execute_query(query, {
            'ticker': params['ticker'],
            'threshold': params['edge_weight_threshold'],
            'top_n': params['top_n']
        })
        
        # Convert results to Cytoscape format
        nodes, edges = _convert_to_cytoscape_format(results)
        
        execution_time = (time.time() - start_time) * 1000
        
        metadata = ResponseMetadata(
            timing={'subgraph_execution': execution_time},
            cache_hit=False,
            confidence=1.0,
            node_count=len(nodes),
            edge_count=len(edges)
        )
        
        response = SubgraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )
        
        logger.info("Subgraph request completed",
                   ticker=params['ticker'],
                   nodes_count=len(nodes),
                   edges_count=len(edges),
                   execution_time=execution_time)
        
        return response
        
    except ValueError as e:
        logger.warning("Subgraph validation failed", error=str(e), ticker=ticker)
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error("Subgraph request failed", error=str(e), ticker=ticker)
        raise HTTPException(status_code=500, detail="Subgraph generation failed. Please try again.")

def _serialize_neo4j_properties(obj):
    """Convert Neo4j objects to serializable dictionaries."""
    if hasattr(obj, '__dict__'):
        # Neo4j Node or Relationship object
        result = dict(obj)
        # Convert any datetime objects to ISO strings
        for key, value in result.items():
            if hasattr(value, 'isoformat'):
                result[key] = value.isoformat()
        return result
    elif isinstance(obj, dict):
        # Already a dictionary
        result = {}
        for key, value in obj.items():
            if hasattr(value, 'isoformat'):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    return {}

def _convert_to_cytoscape_format(results):
    """Convert Neo4j results to Cytoscape nodes and edges format."""
    nodes = []
    edges = []
    seen_nodes = set()
    
    for result in results:
        etf = result.get('e', {})
        company = result.get('c', {})
        sector = result.get('s', {})
        holds_rel = result.get('h', {})
        
        # Add ETF node
        etf_id = f"ETF:{etf.get('ticker', '')}"
        if etf_id not in seen_nodes:
            nodes.append(GraphNode(
                id=etf_id,
                label=etf.get('ticker', ''),
                type="ETF",
                properties=_serialize_neo4j_properties(etf)
            ))
            seen_nodes.add(etf_id)
        
        # Add Company node
        company_id = f"Company:{company.get('symbol', '')}"
        if company_id not in seen_nodes:
            nodes.append(GraphNode(
                id=company_id,
                label=company.get('symbol', ''),
                type="Company",
                properties=_serialize_neo4j_properties(company)
            ))
            seen_nodes.add(company_id)
        
        # Add Sector node
        sector_id = f"Sector:{sector.get('name', '')}"
        if sector_id not in seen_nodes:
            nodes.append(GraphNode(
                id=sector_id,
                label=sector.get('name', ''),
                type="Sector",
                properties=_serialize_neo4j_properties(sector)
            ))
            seen_nodes.add(sector_id)
        
        # Add HOLDS edge (ETF -> Company)
        holds_edge_id = f"holds:{etf_id}:{company_id}"
        edges.append(GraphEdge(
            id=holds_edge_id,
            source=etf_id,
            target=company_id,
            type="HOLDS",
            properties=_serialize_neo4j_properties(holds_rel)
        ))
        
        # Add IN_SECTOR edge (Company -> Sector)
        sector_edge_id = f"in_sector:{company_id}:{sector_id}"
        # Check if this edge already exists
        if not any(edge.id == sector_edge_id for edge in edges):
            edges.append(GraphEdge(
                id=sector_edge_id,
                source=company_id,
                target=sector_id,
                type="IN_SECTOR",
                properties={}
            ))
    
    return nodes, edges

# Initialization function
def initialize_graph_router(neo4j: Neo4jService):
    """Initialize the graph router with Neo4j service."""
    global neo4j_service
    neo4j_service = neo4j
    logger.info("Graph router initialized successfully")