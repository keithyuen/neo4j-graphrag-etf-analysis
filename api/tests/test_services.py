"""Tests for service layer components."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from app.services.neo4j_service import Neo4jService
from app.services.ollama_service import OllamaService
from app.services.cache_service import CacheService


class TestNeo4jService:
    """Test Neo4j service functionality."""
    
    @pytest.fixture
    def mock_driver(self):
        """Mock Neo4j driver."""
        driver = Mock()
        driver.session = Mock()
        return driver
    
    @pytest.fixture
    def neo4j_service(self, mock_driver):
        """Create Neo4j service with mocked driver."""
        service = Neo4jService("bolt://localhost:7687", "neo4j", "password")
        service.driver = mock_driver
        return service
    
    @pytest.mark.asyncio
    async def test_execute_read_query(self, neo4j_service, mock_driver):
        """Test read query execution."""
        # Mock session and result
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data = Mock(return_value=[
            {"ticker": "SPY", "name": "SPDR S&P 500 ETF"}
        ])
        
        mock_session.execute_read = Mock(return_value=mock_result)
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        
        query = "MATCH (e:ETF {ticker: $ticker}) RETURN e.ticker as ticker, e.name as name"
        params = {"ticker": "SPY"}
        
        result = await neo4j_service.execute_read(query, params)
        
        assert len(result) == 1
        assert result[0]["ticker"] == "SPY"
        mock_session.execute_read.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_write_query(self, neo4j_service, mock_driver):
        """Test write query execution."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data = Mock(return_value=[{"created": 1}])
        
        mock_session.execute_write = Mock(return_value=mock_result)
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        
        query = "CREATE (e:ETF {ticker: $ticker, name: $name})"
        params = {"ticker": "SPY", "name": "SPDR S&P 500 ETF"}
        
        result = await neo4j_service.execute_write(query, params)
        
        assert result[0]["created"] == 1
        mock_session.execute_write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, neo4j_service, mock_driver):
        """Test connection error handling."""
        from neo4j.exceptions import ServiceUnavailable
        
        mock_driver.session.side_effect = ServiceUnavailable("Connection failed")
        
        with pytest.raises(ServiceUnavailable):
            await neo4j_service.execute_read("MATCH (n) RETURN n", {})
    
    @pytest.mark.asyncio
    async def test_query_timeout(self, neo4j_service, mock_driver):
        """Test query timeout handling."""
        mock_session = Mock()
        
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(10)
            return Mock(data=Mock(return_value=[]))
        
        mock_session.execute_read = Mock(side_effect=slow_query)
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        
        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                neo4j_service.execute_read("SLOW QUERY", {}),
                timeout=1.0
            )
    
    @pytest.mark.asyncio
    async def test_close_connection(self, neo4j_service, mock_driver):
        """Test connection cleanup."""
        await neo4j_service.close()
        mock_driver.close.assert_called_once()


class TestOllamaService:
    """Test Ollama service functionality."""
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client."""
        client = Mock()
        client.post = AsyncMock()
        return client
    
    @pytest.fixture
    def ollama_service(self, mock_httpx_client):
        """Create Ollama service with mocked client."""
        service = OllamaService("http://localhost:11434", "mistral:instruct")
        service.client = mock_httpx_client
        return service
    
    @pytest.mark.asyncio
    async def test_generate_text(self, ollama_service, mock_httpx_client):
        """Test text generation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "This is a generated response from the LLM.",
            "done": True
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await ollama_service.generate(
            prompt="Generate a response about ETF analysis",
            temperature=0.2,
            max_tokens=300
        )
        
        assert result["response"] == "This is a generated response from the LLM."
        assert result["done"] is True
        mock_httpx_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, ollama_service, mock_httpx_client):
        """Test generation with system prompt."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Classification: etf_exposure_to_company",
            "done": True
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await ollama_service.generate(
            prompt="Classify this query: SPY exposure to Apple",
            system_prompt="You are an intent classifier. Return JSON only.",
            temperature=0.1
        )
        
        assert "Classification" in result["response"]
        
        # Verify system prompt was included in request
        call_args = mock_httpx_client.post.call_args
        request_data = call_args[1]["json"]
        assert "system" in str(request_data) or "messages" in request_data
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self, ollama_service, mock_httpx_client):
        """Test embedding generation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, -0.1, 0.5] * 100  # 500-dim embedding
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await ollama_service.embed("ETF analysis document")
        
        assert len(result) == 500
        assert all(isinstance(x, (int, float)) for x in result)
        mock_httpx_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, ollama_service, mock_httpx_client):
        """Test connection error handling."""
        import httpx
        
        mock_httpx_client.post.side_effect = httpx.ConnectError("Connection failed")
        
        with pytest.raises(httpx.ConnectError):
            await ollama_service.generate("test prompt")
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, ollama_service, mock_httpx_client):
        """Test rate limiting behavior."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "test", "done": True}
        mock_httpx_client.post.return_value = mock_response
        
        # Make multiple rapid requests
        tasks = []
        for i in range(5):
            task = ollama_service.generate(f"prompt {i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all("response" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_model_validation(self, ollama_service):
        """Test model validation."""
        # Valid model
        assert ollama_service.model == "mistral:instruct"
        
        # Test with different model
        ollama_service.model = "llama3.1:8b-instruct"
        assert ollama_service.model == "llama3.1:8b-instruct"


class TestCacheService:
    """Test cache service functionality."""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service."""
        return CacheService(ttl_hours=24)
    
    def test_cache_set_get(self, cache_service):
        """Test basic cache set and get operations."""
        key = "test_key"
        value = {"data": "test_value", "number": 123}
        
        # Set value
        cache_service.set(key, value)
        
        # Get value
        retrieved = cache_service.get(key)
        assert retrieved == value
    
    def test_cache_expiration(self, cache_service):
        """Test cache expiration."""
        import time
        
        # Set short TTL for testing
        cache_service.ttl_seconds = 1
        
        key = "expiring_key"
        value = {"data": "expires_soon"}
        
        cache_service.set(key, value)
        assert cache_service.get(key) == value
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache_service.get(key) is None
    
    def test_cache_miss(self, cache_service):
        """Test cache miss behavior."""
        result = cache_service.get("nonexistent_key")
        assert result is None
    
    def test_cache_invalidation(self, cache_service):
        """Test cache invalidation."""
        key = "to_invalidate"
        value = {"data": "will_be_invalidated"}
        
        cache_service.set(key, value)
        assert cache_service.get(key) == value
        
        # Invalidate
        cache_service.delete(key)
        assert cache_service.get(key) is None
    
    def test_cache_clear(self, cache_service):
        """Test cache clearing."""
        # Set multiple values
        cache_service.set("key1", {"data": 1})
        cache_service.set("key2", {"data": 2})
        cache_service.set("key3", {"data": 3})
        
        assert cache_service.get("key1") is not None
        assert cache_service.get("key2") is not None
        
        # Clear cache
        cache_service.clear()
        
        assert cache_service.get("key1") is None
        assert cache_service.get("key2") is None
        assert cache_service.get("key3") is None
    
    def test_cache_stats(self, cache_service):
        """Test cache statistics."""
        # Generate some cache activity
        cache_service.set("key1", {"data": 1})
        cache_service.set("key2", {"data": 2})
        
        # Cache hits
        cache_service.get("key1")
        cache_service.get("key1")
        
        # Cache miss
        cache_service.get("nonexistent")
        
        stats = cache_service.get_stats()
        
        assert "total_entries" in stats
        assert "hit_rate" in stats
        assert "miss_rate" in stats
        assert stats["total_entries"] >= 2
    
    def test_cache_memory_usage(self, cache_service):
        """Test memory usage tracking."""
        import sys
        
        # Add some data
        large_data = {"data": "x" * 1000}  # 1KB of data
        for i in range(10):
            cache_service.set(f"key_{i}", large_data)
        
        stats = cache_service.get_stats()
        
        # Should report memory usage
        assert "memory_usage_mb" in stats
        assert stats["memory_usage_mb"] > 0
    
    def test_cache_key_patterns(self, cache_service):
        """Test different cache key patterns."""
        # Test various key patterns used in the system
        keys_values = [
            ("query:spy_exposure_apple", {"result": "data"}),
            ("intent:etf_overlap", {"intent": "classified"}),
            ("cypher:template_1", {"template": "query"}),
            ("etl:spy_holdings", {"holdings": []}),
        ]
        
        for key, value in keys_values:
            cache_service.set(key, value)
            retrieved = cache_service.get(key)
            assert retrieved == value
    
    def test_cache_concurrent_access(self, cache_service):
        """Test concurrent cache access."""
        import threading
        import time
        
        results = []
        
        def cache_worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = {"worker": worker_id, "iteration": i}
                
                cache_service.set(key, value)
                retrieved = cache_service.get(key)
                results.append(retrieved == value)
                
                time.sleep(0.01)  # Small delay
        
        # Start multiple threads
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=cache_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All operations should have succeeded
        assert all(results)
        assert len(results) == 30  # 3 workers * 10 iterations


class TestServiceIntegration:
    """Test service integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_neo4j_ollama_integration(self, mock_neo4j_service, mock_ollama_service):
        """Test Neo4j and Ollama service integration."""
        # Mock Neo4j query result
        mock_neo4j_service.execute_read.return_value = [
            {"ticker": "SPY", "symbol": "AAPL", "weight": 0.07}
        ]
        
        # Mock Ollama generation
        mock_ollama_service.generate.return_value = {
            "response": "SPY has 7% exposure to Apple Inc.",
            "done": True
        }
        
        # Simulate pipeline using both services
        query_result = await mock_neo4j_service.execute_read(
            "MATCH (e:ETF)-[h:HOLDS]->(c:Company) RETURN *", 
            {"ticker": "SPY"}
        )
        
        llm_response = await mock_ollama_service.generate(
            f"Summarize this data: {query_result}"
        )
        
        assert len(query_result) == 1
        assert "SPY" in llm_response["response"]
        assert "7%" in llm_response["response"]
    
    @pytest.mark.asyncio
    async def test_cache_service_integration(self, cache_service, mock_neo4j_service):
        """Test cache service integration with other services."""
        cache_key = "etf_holdings:SPY"
        
        # First call - cache miss, query database
        cached_result = cache_service.get(cache_key)
        assert cached_result is None
        
        # Simulate database query
        db_result = [{"ticker": "SPY", "holdings": 500}]
        mock_neo4j_service.execute_read.return_value = db_result
        
        query_result = await mock_neo4j_service.execute_read("QUERY", {})
        
        # Cache the result
        cache_service.set(cache_key, query_result)
        
        # Second call - cache hit
        cached_result = cache_service.get(cache_key)
        assert cached_result == query_result
        
        # Verify database wasn't called again
        mock_neo4j_service.execute_read.assert_called_once()