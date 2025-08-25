from typing import List, Dict, Any, Optional
import re
from pydantic import BaseModel, validator
from config import settings

class QueryValidator:
    """Validation utilities for API requests."""
    
    @staticmethod
    def validate_query_text(query: str) -> str:
        """Validate and clean query text."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # Check length
        if len(cleaned) > settings.max_query_length:
            raise ValueError(f"Query too long. Maximum {settings.max_query_length} characters allowed")
        
        # Check for minimum length
        if len(cleaned) < 3:
            raise ValueError("Query too short. Please provide a more detailed question")
        
        return cleaned
    
    @staticmethod
    def validate_ticker(ticker: str) -> str:
        """Validate ETF ticker format and whitelist."""
        if not ticker:
            raise ValueError("Ticker cannot be empty")
        
        # Clean and uppercase
        cleaned = ticker.strip().upper()
        
        # Check format (2-5 uppercase letters)
        if not re.match(r'^[A-Z]{2,5}$', cleaned):
            raise ValueError("Invalid ticker format. Use 2-5 uppercase letters")
        
        # Check whitelist
        if cleaned not in settings.allowed_tickers:
            allowed_str = ", ".join(settings.allowed_tickers)
            raise ValueError(f"Ticker not supported. Allowed tickers: {allowed_str}")
        
        return cleaned
    
    @staticmethod
    def validate_company_symbol(symbol: str) -> str:
        """Validate company symbol format."""
        if not symbol:
            raise ValueError("Company symbol cannot be empty")
        
        # Clean and uppercase
        cleaned = symbol.strip().upper()
        
        # Check format (1-5 uppercase letters/numbers)
        if not re.match(r'^[A-Z0-9]{1,5}$', cleaned):
            raise ValueError("Invalid company symbol format")
        
        return cleaned
    
    @staticmethod
    def validate_sector_name(sector: str) -> str:
        """Validate sector name format."""
        if not sector:
            raise ValueError("Sector name cannot be empty")
        
        # Clean and title case
        cleaned = sector.strip().title()
        
        # Check length
        if len(cleaned) < 2 or len(cleaned) > 50:
            raise ValueError("Sector name must be 2-50 characters")
        
        # Check format (letters, spaces, hyphens only)
        if not re.match(r'^[A-Za-z\s\-]+$', cleaned):
            raise ValueError("Sector name can only contain letters, spaces, and hyphens")
        
        return cleaned
    
    @staticmethod
    def validate_percentage(value: float) -> float:
        """Validate percentage value (0.0 to 1.0)."""
        if not isinstance(value, (int, float)):
            raise ValueError("Percentage must be a number")
        
        if value < 0.0 or value > 1.0:
            raise ValueError("Percentage must be between 0.0 and 1.0")
        
        return float(value)
    
    @staticmethod
    def validate_count(value: int, min_val: int = 1, max_val: int = None) -> int:
        """Validate count value."""
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError("Count must be an integer")
        
        if value < min_val:
            raise ValueError(f"Count must be at least {min_val}")
        
        if max_val and value > max_val:
            raise ValueError(f"Count cannot exceed {max_val}")
        
        return value
    
    @staticmethod
    def validate_top_n(value: int) -> int:
        """Validate top_n parameter."""
        return QueryValidator.validate_count(value, min_val=1, max_val=settings.max_cypher_limit)

class RequestValidator(BaseModel):
    """Base validator for API requests."""
    
    @validator('*', pre=True)
    def strip_strings(cls, v):
        """Strip whitespace from string values."""
        if isinstance(v, str):
            return v.strip()
        return v

def validate_subgraph_params(ticker: str, top_n: int, edge_weight_threshold: float) -> Dict[str, Any]:
    """Validate subgraph request parameters."""
    validated = {}
    
    # Validate ticker
    validated['ticker'] = QueryValidator.validate_ticker(ticker)
    
    # Validate top_n
    validated['top_n'] = QueryValidator.validate_top_n(top_n)
    
    # Validate edge weight threshold
    validated['edge_weight_threshold'] = QueryValidator.validate_percentage(edge_weight_threshold)
    
    return validated

def validate_etl_params(tickers: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
    """Validate ETL request parameters."""
    validated = {}
    
    if tickers:
        # Validate each ticker
        validated_tickers = []
        for ticker in tickers:
            validated_tickers.append(QueryValidator.validate_ticker(ticker))
        validated['tickers'] = validated_tickers
    else:
        validated['tickers'] = None
    
    validated['force'] = bool(force)
    
    return validated