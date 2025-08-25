from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"
    neo4j_database: str = "neo4j"
    
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral:instruct"
    ollama_temperature: float = 0.2
    ollama_max_tokens: int = 500
    
    # Security Configuration
    allowed_tickers: List[str] = ["SPY", "QQQ", "IWM", "IJH", "IVE", "IVW"]
    max_query_length: int = 512
    max_cypher_limit: int = 50
    
    # Cache Configuration
    response_cache_ttl: int = 3600
    
    # Logging Configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()