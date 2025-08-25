from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .entities import GroundedEntity

class ResponseMetadata(BaseModel):
    timing: Dict[str, float]
    cache_hit: bool = False
    confidence: float
    node_count: Optional[int] = None
    edge_count: Optional[int] = None
    pipeline_version: str = "1.0.0"

class GraphRAGResponse(BaseModel):
    answer: str                           # LLM synthesized answer (mandatory)
    rows: List[Dict[str, Any]]           # Cypher query results
    intent: str                          # Classified intent key
    cypher: str                          # Executed Cypher query
    entities: List[GroundedEntity]       # Grounded entities
    metadata: ResponseMetadata           # Execution metadata

class IntentResponse(BaseModel):
    intent: str
    confidence: float
    entities: List[GroundedEntity]
    required_parameters: List[str]
    missing_parameters: List[str]

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class SubgraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: ResponseMetadata

class ETLResponse(BaseModel):
    success: bool
    message: str
    tickers_processed: List[str]
    cache_stats: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, bool]