from pydantic import BaseModel, Field
from typing import Optional, List

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="User query about ETF data")

class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="Query for intent classification")

class SubgraphRequest(BaseModel):
    ticker: str = Field(..., description="ETF ticker symbol")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of top holdings")
    edge_weight_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum edge weight to include")

class ETLRefreshRequest(BaseModel):
    tickers: Optional[List[str]] = Field(default=None, description="Specific tickers to refresh, or all if None")
    force: bool = Field(default=False, description="Force refresh ignoring cache TTL")