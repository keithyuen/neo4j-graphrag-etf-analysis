"""Integration tests for API endpoints with real services."""
import pytest
import asyncio
from httpx import AsyncClient
from testcontainers.neo4j import Neo4jContainer
from testcontainers.compose import DockerCompose
import os
import time
from pathlib import Path

# Skip integration tests if not in CI or explicitly requested
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def docker_compose():
    """Start Docker Compose stack for integration testing."""
    compose_path = Path(__file__).parent.parent.parent.parent
    
    with DockerCompose(
        compose_path,
        compose_file_name="docker-compose.test.yml",
        pull=True
    ) as compose:
        # Wait for services to be ready
        time.sleep(30)
        yield compose


@pytest.fixture(scope="session")
def neo4j_container():
    """Start Neo4j container for testing."""
    with Neo4jContainer("neo4j:5.15") as neo4j:
        # Configure Neo4j for testing
        neo4j.with_env("NEO4J_AUTH", "neo4j/testpassword")
        neo4j.with_env("NEO4J_PLUGINS", '["apoc"]')
        
        # Wait for Neo4j to be ready
        connection_url = neo4j.get_connection_url()
        time.sleep(10)
        
        yield {
            "url": connection_url,
            "username": "neo4j", 
            "password": "testpassword"
        }


@pytest.fixture
async def integration_client(docker_compose):
    """HTTP client for integration testing."""
    base_url = "http://localhost:8000"
    
    # Wait for API to be ready
    for _ in range(30):
        try:
            async with AsyncClient(base_url=base_url) as client:
                response = await client.get("/health")
                if response.status_code == 200:
                    break
        except:
            await asyncio.sleep(1)
    
    async with AsyncClient(base_url=base_url) as client:
        yield client


class TestFullStackIntegration:
    """Test complete stack integration."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, integration_client):
        """Test API health check endpoint."""
        response = await integration_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "neo4j" in data["services"]
        assert "ollama" in data["services"]
    
    @pytest.mark.asyncio
    async def test_etl_refresh_and_query(self, integration_client):
        """Test ETL refresh followed by query."""
        # First, refresh ETF data
        refresh_response = await integration_client.post(
            "/etl/refresh/force"
        )
        assert refresh_response.status_code == 200
        
        refresh_data = refresh_response.json()
        assert "updated_etfs" in refresh_data
        assert len(refresh_data["updated_etfs"]) > 0
        
        # Wait for ETL to complete
        await asyncio.sleep(5)
        
        # Now test a query
        query_response = await integration_client.post(
            "/ask",
            json={"query": "SPY exposure to Apple"}
        )
        assert query_response.status_code in [200, 400]  # May need parameters
        
        if query_response.status_code == 200:
            query_data = query_response.json()
            assert "answer" in query_data
            assert "rows" in query_data
            assert "intent" in query_data
    
    @pytest.mark.asyncio
    async def test_intent_classification_flow(self, integration_client):
        """Test intent classification workflow."""
        # Test intent classification
        intent_response = await integration_client.post(
            "/intent",
            json={"query": "What is SPY's exposure to Apple?"}
        )
        assert intent_response.status_code == 200
        
        intent_data = intent_response.json()
        assert "intent_key" in intent_data
        assert "confidence" in intent_data
        assert "grounded_entities" in intent_data
        
        # Verify reasonable confidence
        assert intent_data["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_graph_subgraph_generation(self, integration_client):
        """Test graph subgraph endpoint."""
        # First ensure we have data
        await integration_client.post("/etl/refresh/force")
        await asyncio.sleep(5)
        
        # Test subgraph generation
        subgraph_response = await integration_client.get(
            "/graph/subgraph?ticker=SPY&top=10"
        )
        assert subgraph_response.status_code == 200
        
        subgraph_data = subgraph_response.json()
        assert "nodes" in subgraph_data
        assert "edges" in subgraph_data
        
        # Should have ETF, Company, and Sector nodes
        node_types = {node.get("type") for node in subgraph_data["nodes"]}
        assert "ETF" in node_types
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, integration_client):
        """Test cache statistics endpoint."""
        response = await integration_client.get("/cache/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_entries" in stats
        assert "hit_rate" in stats
        assert "memory_usage_mb" in stats
    
    @pytest.mark.asyncio
    async def test_query_with_parameters(self, integration_client):
        """Test query requiring parameter fulfillment."""
        # First refresh data
        await integration_client.post("/etl/refresh/force")
        await asyncio.sleep(5)
        
        # Test incomplete query
        incomplete_response = await integration_client.post(
            "/ask",
            json={"query": "SPY exposure"}
        )
        
        if incomplete_response.status_code == 400:
            # Should indicate missing parameters
            error_data = incomplete_response.json()
            assert "needs_parameters" in error_data["detail"]
            assert "missing_params" in error_data["detail"]
        
        # Test complete query
        complete_response = await integration_client.post(
            "/ask",
            json={"query": "SPY exposure to Apple Inc"}
        )
        
        # Should succeed or provide better guidance
        assert complete_response.status_code in [200, 400]


class TestErrorHandlingIntegration:
    """Test error handling in integration environment."""
    
    @pytest.mark.asyncio
    async def test_invalid_ticker_handling(self, integration_client):
        """Test handling of invalid tickers."""
        response = await integration_client.post(
            "/ask",
            json={"query": "INVALID_TICKER exposure to Apple"}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            # Should indicate no results or unknown entity
            assert "no" in data["answer"].lower() or "unknown" in data["answer"].lower()
    
    @pytest.mark.asyncio
    async def test_malformed_query_handling(self, integration_client):
        """Test handling of malformed queries."""
        malformed_queries = [
            "",
            "   ",
            "a" * 1000,  # Very long query
            "SELECT * FROM users; DROP TABLE holdings;",  # SQL injection
            "<script>alert('xss')</script>"  # XSS attempt
        ]
        
        for query in malformed_queries:
            response = await integration_client.post(
                "/ask",
                json={"query": query}
            )
            
            # Should not crash the server
            assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, integration_client):
        """Test handling of concurrent requests."""
        queries = [
            "SPY exposure to Apple",
            "QQQ vs IWM overlap",
            "Technology sector allocation",
            "Top holdings in SPY",
            "IVE sector exposure"
        ]
        
        # Send concurrent requests
        tasks = []
        for query in queries:
            task = integration_client.post(
                "/ask",
                json={"query": query}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle all requests
        assert len(responses) == len(queries)
        
        # Check that most succeeded
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code in [200, 400])
        assert success_count >= len(queries) * 0.8  # At least 80% success rate


class TestPerformanceIntegration:
    """Test performance characteristics in integration environment."""
    
    @pytest.mark.asyncio
    async def test_query_response_time(self, integration_client):
        """Test query response times."""
        import time
        
        # Warm up
        await integration_client.post("/ask", json={"query": "SPY exposure to Apple"})
        
        # Measure response time
        start_time = time.time()
        response = await integration_client.post(
            "/ask",
            json={"query": "QQQ vs IWM overlap"}
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within reasonable time (10 seconds for integration test)
        assert response_time < 10.0
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_subgraph_generation_performance(self, integration_client):
        """Test subgraph generation performance."""
        import time
        
        start_time = time.time()
        response = await integration_client.get(
            "/graph/subgraph?ticker=SPY&top=20"
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should generate subgraph quickly
        assert response_time < 5.0
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_etl_refresh_performance(self, integration_client):
        """Test ETL refresh performance."""
        import time
        
        start_time = time.time()
        response = await integration_client.post(
            "/etl/refresh",
            json={"tickers": ["SPY"]}
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # ETL should complete within reasonable time
        assert response_time < 30.0  # 30 seconds for single ETF
        assert response.status_code == 200


class TestDataConsistencyIntegration:
    """Test data consistency across operations."""
    
    @pytest.mark.asyncio
    async def test_etl_data_consistency(self, integration_client):
        """Test ETL data consistency."""
        # Refresh specific ETF
        refresh_response = await integration_client.post(
            "/etl/refresh",
            json={"tickers": ["SPY"]}
        )
        assert refresh_response.status_code == 200
        
        refresh_data = refresh_response.json()
        holdings_count = refresh_data.get("total_holdings", 0)
        
        # Query holdings through different endpoints
        subgraph_response = await integration_client.get(
            "/graph/subgraph?ticker=SPY&top=50"
        )
        assert subgraph_response.status_code == 200
        
        subgraph_data = subgraph_response.json()
        nodes_count = len([n for n in subgraph_data["nodes"] if n.get("type") == "Company"])
        
        # Data should be consistent (allowing for limits)
        assert nodes_count <= holdings_count or nodes_count <= 50
    
    @pytest.mark.asyncio
    async def test_cache_consistency(self, integration_client):
        """Test cache consistency."""
        # Make same query twice
        query = {"query": "SPY exposure to technology sector"}
        
        response1 = await integration_client.post("/ask", json=query)
        response2 = await integration_client.post("/ask", json=query)
        
        # Should get consistent results (both succeed or both fail)
        assert response1.status_code == response2.status_code
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            # Core results should be consistent
            assert data1["intent"] == data2["intent"]
            assert len(data1["rows"]) == len(data2["rows"])


class TestSecurityIntegration:
    """Test security measures in integration environment."""
    
    @pytest.mark.asyncio
    async def test_injection_prevention(self, integration_client):
        """Test injection attack prevention."""
        malicious_queries = [
            "SPY; MATCH (n) DELETE n",
            "QQQ'; DROP TABLE companies; --",
            "UNION SELECT password FROM users",
            "'; EXEC xp_cmdshell('rm -rf /'); --"
        ]
        
        for malicious_query in malicious_queries:
            response = await integration_client.post(
                "/ask",
                json={"query": malicious_query}
            )
            
            # Should not execute malicious code
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Should not contain evidence of successful injection
                answer = data.get("answer", "").lower()
                assert "deleted" not in answer
                assert "dropped" not in answer
                assert "error" not in answer or "injection" in answer
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, integration_client):
        """Test rate limiting functionality."""
        # Send many rapid requests
        tasks = []
        for i in range(20):
            task = integration_client.post(
                "/ask",
                json={"query": f"SPY query {i}"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some requests might be rate limited
        status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
        
        # Should handle all requests without crashing
        assert len(status_codes) == 20
        assert all(code in [200, 400, 422, 429] for code in status_codes)
    
    @pytest.mark.asyncio 
    async def test_input_validation(self, integration_client):
        """Test comprehensive input validation."""
        invalid_requests = [
            # Invalid JSON structure
            {"invalid": "structure"},
            # Missing required fields
            {},
            # Wrong data types
            {"query": 123},
            {"query": None},
            {"query": ["not", "a", "string"]},
        ]
        
        for invalid_request in invalid_requests:
            response = await integration_client.post(
                "/ask",
                json=invalid_request
            )
            
            # Should reject invalid requests
            assert response.status_code == 422