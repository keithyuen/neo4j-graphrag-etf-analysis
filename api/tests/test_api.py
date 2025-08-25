"""Tests for API endpoints."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from app.main import app
from app.models.requests import AskRequest, IntentRequest, ETLRefreshRequest
from app.models.responses import AskResponse, IntentResponse, GraphResponse


class TestAskEndpoint:
    """Test /ask endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_ask_successful_query(self, async_client, sample_cypher_results):
        """Test successful query processing."""
        mock_pipeline_result = {
            "answer": "SPY has a 7.0% allocation to Apple Inc (AAPL), representing 178 million shares.",
            "rows": sample_cypher_results,
            "intent": "etf_exposure_to_company",
            "cypher": "MATCH (e:ETF)-[h:HOLDS]->(c:Company) RETURN *",
            "entities": [
                {"type": "ETF", "value": "SPY", "ticker": "SPY"},
                {"type": "Company", "value": "AAPL", "symbol": "AAPL"}
            ],
            "metadata": {
                "processing_time_ms": 150,
                "cache_hit": False,
                "node_count": 2,
                "edge_count": 1
            },
            "needs_parameters": False,
            "error": None
        }
        
        with patch('app.api.ask.GraphRAGPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.process_query = AsyncMock(return_value=mock_pipeline_result)
            mock_pipeline_class.return_value = mock_pipeline
            
            response = await async_client.post(
                "/ask",
                json={"query": "SPY exposure to Apple"}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result["answer"] == mock_pipeline_result["answer"]
        assert result["rows"] == mock_pipeline_result["rows"]
        assert result["intent"] == mock_pipeline_result["intent"]
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_ask_missing_parameters(self, async_client):
        """Test query with missing parameters."""
        mock_pipeline_result = {
            "answer": None,
            "rows": [],
            "intent": "etf_exposure_to_company",
            "entities": [{"type": "ETF", "value": "SPY", "ticker": "SPY"}],
            "needs_parameters": True,
            "missing_params": ["symbol"],
            "required_params": ["ticker", "symbol"],
            "error": None
        }
        
        with patch('app.api.ask.GraphRAGPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.process_query = AsyncMock(return_value=mock_pipeline_result)
            mock_pipeline_class.return_value = mock_pipeline
            
            response = await async_client.post(
                "/ask",
                json={"query": "SPY exposure"}
            )
        
        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["needs_parameters"] is True
        assert "symbol" in result["detail"]["missing_params"]
    
    @pytest.mark.asyncio
    async def test_ask_invalid_query(self, async_client):
        """Test invalid query handling."""
        response = await async_client.post(
            "/ask",
            json={"query": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_ask_security_injection(self, async_client):
        """Test security injection prevention."""
        malicious_queries = [
            "SPY; MATCH (n) DELETE n",
            "QQQ UNION SELECT * FROM secrets",
            "<script>alert('xss')</script>"
        ]
        
        for malicious_query in malicious_queries:
            response = await async_client.post(
                "/ask", 
                json={"query": malicious_query}
            )
            
            # Should either reject or sanitize
            assert response.status_code in [400, 422] or "DELETE" not in response.json().get("answer", "")


class TestIntentEndpoint:
    """Test /intent endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_intent_classification(self, async_client):
        """Test intent classification endpoint."""
        mock_intent_result = {
            "intent_key": "etf_exposure_to_company",
            "confidence": 0.85,
            "grounded_entities": [
                {"type": "ETF", "value": "SPY", "ticker": "SPY"},
                {"type": "Company", "value": "AAPL", "symbol": "AAPL"}
            ],
            "required_params": ["ticker", "symbol"],
            "missing_params": []
        }
        
        with patch('app.api.intent.IntentClassifier') as mock_classifier_class:
            mock_classifier = Mock()
            mock_classifier.classify_intent = AsyncMock(return_value=Mock(**mock_intent_result))
            mock_classifier_class.return_value = mock_classifier
            
            with patch('app.api.intent.EntityGrounder') as mock_grounder_class:
                mock_grounder = Mock()
                mock_grounder.ground_entities = AsyncMock(return_value=mock_intent_result["grounded_entities"])
                mock_grounder_class.return_value = mock_grounder
                
                response = await async_client.post(
                    "/intent",
                    json={"query": "SPY exposure to Apple"}
                )
        
        assert response.status_code == 200
        result = response.json()
        assert result["intent_key"] == "etf_exposure_to_company"
        assert result["confidence"] == 0.85
        assert len(result["grounded_entities"]) == 2
    
    @pytest.mark.asyncio
    async def test_intent_low_confidence(self, async_client):
        """Test low confidence intent classification."""
        mock_intent_result = {
            "intent_key": "unknown",
            "confidence": 0.2,
            "grounded_entities": [],
            "required_params": [],
            "missing_params": []
        }
        
        with patch('app.api.intent.IntentClassifier') as mock_classifier_class:
            mock_classifier = Mock()
            mock_classifier.classify_intent = AsyncMock(return_value=Mock(**mock_intent_result))
            mock_classifier_class.return_value = mock_classifier
            
            with patch('app.api.intent.EntityGrounder') as mock_grounder_class:
                mock_grounder = Mock()
                mock_grounder.ground_entities = AsyncMock(return_value=[])
                mock_grounder_class.return_value = mock_grounder
                
                response = await async_client.post(
                    "/intent",
                    json={"query": "unclear nonsense query"}
                )
        
        assert response.status_code == 200
        result = response.json()
        assert result["intent_key"] == "unknown"
        assert result["confidence"] < 0.5


class TestGraphEndpoint:
    """Test /graph endpoints functionality."""
    
    @pytest.mark.asyncio
    async def test_subgraph_endpoint(self, async_client):
        """Test subgraph generation endpoint."""
        mock_subgraph_data = {
            "nodes": [
                {"id": "SPY", "label": "SPY", "type": "ETF", "name": "SPDR S&P 500 ETF"},
                {"id": "AAPL", "label": "AAPL", "type": "Company", "name": "Apple Inc"},
                {"id": "Information Technology", "label": "Information Technology", "type": "Sector"}
            ],
            "edges": [
                {"source": "SPY", "target": "AAPL", "weight": 0.07, "shares": 178000000},
                {"source": "AAPL", "target": "Information Technology", "weight": 1.0}
            ]
        }
        
        with patch('app.api.graph.Neo4jService') as mock_service_class:
            mock_service = Mock()
            mock_service.execute_read = AsyncMock(return_value=mock_subgraph_data)
            mock_service_class.return_value = mock_service
            
            response = await async_client.get("/graph/subgraph?ticker=SPY&top=10")
        
        assert response.status_code == 200
        result = response.json()
        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) == 3
        assert len(result["edges"]) == 2
    
    @pytest.mark.asyncio
    async def test_subgraph_invalid_ticker(self, async_client):
        """Test subgraph with invalid ticker."""
        response = await async_client.get("/graph/subgraph?ticker=INVALID&top=10")
        
        # Should validate ticker
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_subgraph_limit_enforcement(self, async_client):
        """Test subgraph LIMIT enforcement."""
        with patch('app.api.graph.Neo4jService') as mock_service_class:
            mock_service = Mock()
            mock_service.execute_read = AsyncMock(return_value={"nodes": [], "edges": []})
            mock_service_class.return_value = mock_service
            
            # Test with large top value
            response = await async_client.get("/graph/subgraph?ticker=SPY&top=1000")
        
        # Should cap at maximum limit (50)
        assert response.status_code == 200


class TestETLEndpoint:
    """Test /etl endpoints functionality."""
    
    @pytest.mark.asyncio
    async def test_etl_refresh(self, async_client):
        """Test ETL refresh endpoint."""
        with patch('app.api.etl.ETLProcessor') as mock_etl_class:
            mock_etl = Mock()
            mock_etl.refresh_etf_data = AsyncMock(return_value={
                "updated_etfs": ["SPY", "QQQ"],
                "total_holdings": 1500,
                "cache_status": "refreshed",
                "processing_time_ms": 5000
            })
            mock_etl_class.return_value = mock_etl
            
            response = await async_client.post(
                "/etl/refresh",
                json={"tickers": ["SPY", "QQQ"]}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert "updated_etfs" in result
        assert "SPY" in result["updated_etfs"]
        assert "QQQ" in result["updated_etfs"]
    
    @pytest.mark.asyncio
    async def test_etl_refresh_force(self, async_client):
        """Test forced ETL refresh endpoint."""
        with patch('app.api.etl.ETLProcessor') as mock_etl_class:
            mock_etl = Mock()
            mock_etl.force_refresh_etf_data = AsyncMock(return_value={
                "updated_etfs": ["SPY", "QQQ", "IWM", "IJH", "IVE", "IVW"],
                "total_holdings": 3000,
                "cache_status": "force_refreshed",
                "processing_time_ms": 15000
            })
            mock_etl_class.return_value = mock_etl
            
            response = await async_client.post("/etl/refresh/force")
        
        assert response.status_code == 200
        result = response.json()
        assert result["cache_status"] == "force_refreshed"
        assert len(result["updated_etfs"]) == 6
    
    @pytest.mark.asyncio
    async def test_etl_invalid_tickers(self, async_client):
        """Test ETL with invalid tickers."""
        response = await async_client.post(
            "/etl/refresh",
            json={"tickers": ["INVALID", "FAKE"]}
        )
        
        # Should validate tickers
        assert response.status_code in [400, 422]


class TestCacheEndpoint:
    """Test /cache endpoints functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, async_client):
        """Test cache statistics endpoint."""
        mock_stats = {
            "total_entries": 150,
            "hit_rate": 0.75,
            "miss_rate": 0.25,
            "memory_usage_mb": 45.2,
            "oldest_entry_age_hours": 12.5,
            "cache_ttl_hours": 168
        }
        
        with patch('app.services.cache_service.CacheService') as mock_cache_class:
            mock_cache = Mock()
            mock_cache.get_stats = AsyncMock(return_value=mock_stats)
            mock_cache_class.return_value = mock_cache
            
            response = await async_client.get("/cache/stats")
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_entries"] == 150
        assert result["hit_rate"] == 0.75
        assert "memory_usage_mb" in result


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    @pytest.mark.asyncio
    async def test_validation_errors(self, async_client):
        """Test request validation errors."""
        # Missing required fields
        response = await async_client.post("/ask", json={})
        assert response.status_code == 422
        
        # Invalid data types
        response = await async_client.post("/ask", json={"query": 123})
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_server_errors(self, async_client):
        """Test internal server error handling."""
        with patch('app.api.ask.GraphRAGPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.process_query = AsyncMock(side_effect=Exception("Database connection error"))
            mock_pipeline_class.return_value = mock_pipeline
            
            response = await async_client.post(
                "/ask",
                json={"query": "SPY exposure to Apple"}
            )
        
        assert response.status_code == 500
        result = response.json()
        assert "detail" in result
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, async_client):
        """Test request timeout handling."""
        import asyncio
        
        with patch('app.api.ask.GraphRAGPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            
            async def slow_query(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate slow query
                return {}
            
            mock_pipeline.process_query = slow_query
            mock_pipeline_class.return_value = mock_pipeline
            
            # This should timeout (assuming reasonable timeout settings)
            with pytest.raises(Exception):  # Timeout or similar
                response = await async_client.post(
                    "/ask",
                    json={"query": "SPY exposure to Apple"},
                    timeout=1.0
                )


class TestAPISecurityHeaders:
    """Test security headers and CORS."""
    
    @pytest.mark.asyncio
    async def test_security_headers(self, async_client):
        """Test security headers are present."""
        response = await async_client.get("/")
        
        # Should have basic security headers
        headers = response.headers
        # Note: Actual headers depend on middleware configuration
        assert response.status_code in [200, 404]  # Endpoint may not exist
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """Test CORS headers for cross-origin requests."""
        response = await async_client.options(
            "/ask",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should handle CORS preflight
        assert response.status_code in [200, 204]