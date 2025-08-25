"""Test configuration and fixtures."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from neo4j import AsyncGraphDatabase
from httpx import AsyncClient
from app.main import app
from app.core.config import get_settings
from app.services.neo4j_service import Neo4jService
from app.services.ollama_service import OllamaService


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = get_settings()
    settings.NEO4J_URI = "bolt://localhost:7687"
    settings.NEO4J_USERNAME = "neo4j"
    settings.NEO4J_PASSWORD = "password"
    settings.OLLAMA_HOST = "http://localhost:11434"
    settings.OLLAMA_MODEL = "mistral:instruct"
    settings.ALLOWED_TICKERS = ["SPY", "QQQ", "IWM", "IJH", "IVE", "IVW"]
    return settings


@pytest.fixture
def mock_neo4j_service():
    """Mock Neo4j service."""
    service = Mock(spec=Neo4jService)
    service.driver = Mock()
    service.execute_read = AsyncMock()
    service.execute_write = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def mock_ollama_service():
    """Mock Ollama service."""
    service = Mock(spec=OllamaService)
    service.generate = AsyncMock()
    service.embed = AsyncMock()
    return service


@pytest.fixture
async def async_client():
    """Async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_etf_data():
    """Sample ETF data for testing."""
    return [
        {
            "etf": "SPY",
            "symbol": "AAPL",
            "name": "Apple Inc",
            "sector": "Information Technology",
            "weight": 0.07,
            "shares": 178000000
        },
        {
            "etf": "SPY",
            "symbol": "MSFT", 
            "name": "Microsoft Corp",
            "sector": "Information Technology",
            "weight": 0.065,
            "shares": 165000000
        },
        {
            "etf": "QQQ",
            "symbol": "AAPL",
            "name": "Apple Inc",
            "sector": "Information Technology", 
            "weight": 0.08,
            "shares": 189000000
        }
    ]


@pytest.fixture
def sample_cypher_results():
    """Sample Cypher query results."""
    return [
        {
            "etf_ticker": "SPY",
            "company_symbol": "AAPL",
            "company_name": "Apple Inc",
            "weight": 0.07,
            "shares": 178000000
        },
        {
            "etf_ticker": "QQQ", 
            "company_symbol": "AAPL",
            "company_name": "Apple Inc",
            "weight": 0.08,
            "shares": 189000000
        }
    ]


@pytest.fixture
def sample_intent_data():
    """Sample intent classification data."""
    return {
        "intent_key": "etf_exposure_to_company",
        "confidence": 0.85,
        "grounded_entities": [
            {"type": "ETF", "value": "SPY", "ticker": "SPY"},
            {"type": "Company", "value": "Apple", "symbol": "AAPL"}
        ],
        "required_params": ["ticker", "symbol"],
        "missing_params": []
    }


@pytest.fixture  
def sample_llm_responses():
    """Sample LLM responses for testing."""
    return {
        "intent_classification": {
            "intent_key": "etf_exposure_to_company",
            "confidence": 0.85
        },
        "synthesis": "SPY has a 7.0% allocation to Apple Inc (AAPL), representing 178 million shares worth approximately $32.1 billion. This makes Apple the largest holding in SPY, demonstrating the ETF's significant exposure to large-cap technology stocks."
    }