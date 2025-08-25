from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class EntityType(str, Enum):
    ETF = "ETF"
    COMPANY = "Company"  
    SECTOR = "Sector"
    PERCENT = "Percent"
    COUNT = "Count"

class GroundedEntity(BaseModel):
    name: str
    type: EntityType
    confidence: float = Field(ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)

class IntentResult(BaseModel):
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    entities: List[GroundedEntity]
    required_parameters: List[str]
    
class ParameterFulfillment(BaseModel):
    parameters: Dict[str, Any]
    missing_parameters: List[str]
    is_complete: bool

class CypherResult(BaseModel):
    query: str
    parameters: Dict[str, Any]
    rows: List[Dict[str, Any]]
    execution_time_ms: float
    node_count: Optional[int] = None
    edge_count: Optional[int] = None
    comprehensive_context: Optional[List[Dict[str, Any]]] = None
    is_comprehensive_fallback: Optional[bool] = None

class PreprocessedText(BaseModel):
    normalized_text: str
    extracted_numbers: Dict[str, List[float]]
    potential_tickers: List[str]
    tokens: List[str]
    original_text: str