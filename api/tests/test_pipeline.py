"""Tests for GraphRAG pipeline components."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.graphrag.pipeline import GraphRAGPipeline
from app.graphrag.preprocessor import TextPreprocessor
from app.graphrag.entity_grounder import EntityGrounder
from app.graphrag.intent_classifier import IntentClassifier
from app.graphrag.llm_synthesizer import LLMSynthesizer
from app.models.entities import Intent, Entity


class TestTextPreprocessor:
    """Test text preprocessing functionality."""
    
    def test_normalize_text(self):
        """Test text normalization."""
        preprocessor = TextPreprocessor()
        
        # Basic normalization
        result = preprocessor.normalize("  SPY vs QQQ Overlap?  ")
        assert result == "spy vs qqq overlap"
        
        # Remove special characters
        result = preprocessor.normalize("What's the top 10 holdings!")
        assert result == "whats the top 10 holdings"
    
    def test_extract_numbers(self):
        """Test number extraction."""
        preprocessor = TextPreprocessor()
        
        # Percentage extraction
        numbers = preprocessor.extract_numbers("ETFs with >= 30% tech exposure")
        assert 30.0 in numbers
        
        # Count extraction
        numbers = preprocessor.extract_numbers("top 15 holdings")
        assert 15 in numbers
        
        # Decimal extraction
        numbers = preprocessor.extract_numbers("weight of 0.75")
        assert 0.75 in numbers
    
    def test_tokenize(self):
        """Test tokenization."""
        preprocessor = TextPreprocessor()
        
        tokens = preprocessor.tokenize("SPY QQQ overlap analysis")
        assert tokens == ["spy", "qqq", "overlap", "analysis"]
        
        # Handle punctuation
        tokens = preprocessor.tokenize("What's the SPY-QQQ overlap?")
        assert "spy" in tokens
        assert "qqq" in tokens
        assert "overlap" in tokens


class TestEntityGrounder:
    """Test entity grounding functionality."""
    
    @pytest.fixture
    def mock_neo4j_service(self):
        """Mock Neo4j service for entity grounding."""
        service = Mock()
        service.execute_read = AsyncMock()
        return service
    
    @pytest.fixture
    def entity_grounder(self, mock_neo4j_service):
        """Create entity grounder with mocked service."""
        return EntityGrounder(mock_neo4j_service)
    
    @pytest.mark.asyncio
    async def test_ground_etf_ticker(self, entity_grounder, mock_neo4j_service):
        """Test ETF ticker grounding."""
        # Mock Neo4j response
        mock_neo4j_service.execute_read.return_value = [
            {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust"}
        ]
        
        entities = await entity_grounder.ground_entities(["spy"])
        
        assert len(entities) == 1
        assert entities[0].type == "ETF"
        assert entities[0].value == "SPY"
        assert entities[0].ticker == "SPY"
    
    @pytest.mark.asyncio
    async def test_ground_company_symbol(self, entity_grounder, mock_neo4j_service):
        """Test company symbol grounding."""
        mock_neo4j_service.execute_read.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc"}
        ]
        
        entities = await entity_grounder.ground_entities(["aapl"])
        
        assert len(entities) == 1
        assert entities[0].type == "Company"
        assert entities[0].value == "AAPL"
        assert entities[0].symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_ground_sector(self, entity_grounder, mock_neo4j_service):
        """Test sector grounding."""
        mock_neo4j_service.execute_read.return_value = [
            {"name": "Information Technology"}
        ]
        
        entities = await entity_grounder.ground_entities(["technology", "tech"])
        
        assert len(entities) == 1
        assert entities[0].type == "Sector"
        assert entities[0].value == "Information Technology"
    
    @pytest.mark.asyncio
    async def test_resolve_synonyms(self, entity_grounder, mock_neo4j_service):
        """Test synonym resolution."""
        mock_neo4j_service.execute_read.return_value = [
            {"entity_type": "Sector", "entity_value": "Information Technology"}
        ]
        
        entities = await entity_grounder.ground_entities(["tech", "it"])
        
        # Should resolve tech/IT to Information Technology
        mock_neo4j_service.execute_read.assert_called()


class TestIntentClassifier:
    """Test intent classification functionality."""
    
    @pytest.fixture
    def mock_ollama_service(self):
        """Mock Ollama service for intent classification."""
        service = Mock()
        service.generate = AsyncMock()
        return service
    
    @pytest.fixture
    def intent_classifier(self, mock_ollama_service, mock_neo4j_service):
        """Create intent classifier with mocked services."""
        return IntentClassifier(mock_ollama_service, mock_neo4j_service)
    
    @pytest.mark.asyncio
    async def test_classify_etf_exposure_intent(self, intent_classifier, mock_ollama_service):
        """Test ETF exposure intent classification."""
        # Mock LLM response
        mock_ollama_service.generate.return_value = {
            "response": '{"intent_key": "etf_exposure_to_company", "confidence": 0.85}'
        }
        
        entities = [
            Entity(type="ETF", value="SPY", ticker="SPY"),
            Entity(type="Company", value="AAPL", symbol="AAPL")
        ]
        
        result = await intent_classifier.classify_intent("SPY exposure to Apple", entities)
        
        assert result.intent_key == "etf_exposure_to_company"
        assert result.confidence == 0.85
        assert result.grounded_entities == entities
    
    @pytest.mark.asyncio
    async def test_classify_overlap_intent(self, intent_classifier, mock_ollama_service):
        """Test ETF overlap intent classification."""
        mock_ollama_service.generate.return_value = {
            "response": '{"intent_key": "etf_overlap_weighted", "confidence": 0.90}'
        }
        
        entities = [
            Entity(type="ETF", value="SPY", ticker="SPY"),
            Entity(type="ETF", value="QQQ", ticker="QQQ")
        ]
        
        result = await intent_classifier.classify_intent("overlap between SPY and QQQ", entities)
        
        assert result.intent_key == "etf_overlap_weighted"
        assert result.confidence == 0.90
    
    @pytest.mark.asyncio
    async def test_low_confidence_intent(self, intent_classifier, mock_ollama_service):
        """Test handling of low confidence intent classification."""
        mock_ollama_service.generate.return_value = {
            "response": '{"intent_key": "unknown", "confidence": 0.3}'
        }
        
        result = await intent_classifier.classify_intent("unclear query", [])
        
        assert result.intent_key == "unknown"
        assert result.confidence == 0.3


class TestLLMSynthesizer:
    """Test LLM answer synthesis functionality."""
    
    @pytest.fixture
    def mock_ollama_service(self):
        """Mock Ollama service for synthesis."""
        service = Mock()
        service.generate = AsyncMock()
        return service
    
    @pytest.fixture
    def llm_synthesizer(self, mock_ollama_service):
        """Create LLM synthesizer with mocked service."""
        return LLMSynthesizer(mock_ollama_service)
    
    @pytest.mark.asyncio
    async def test_synthesize_with_results(self, llm_synthesizer, mock_ollama_service, sample_cypher_results):
        """Test synthesis with query results."""
        mock_ollama_service.generate.return_value = {
            "response": "SPY has a 7.0% allocation to Apple Inc (AAPL), representing 178 million shares. QQQ has an 8.0% allocation to Apple, showing both ETFs have significant exposure to this technology stock."
        }
        
        result = await llm_synthesizer.synthesize_answer(
            query="SPY and QQQ exposure to Apple",
            intent="etf_exposure_to_company",
            rows=sample_cypher_results,
            entities=[
                Entity(type="ETF", value="SPY", ticker="SPY"),
                Entity(type="ETF", value="QQQ", ticker="QQQ"),
                Entity(type="Company", value="AAPL", symbol="AAPL")
            ]
        )
        
        assert "7.0%" in result
        assert "8.0%" in result
        assert "Apple" in result
        assert len(result) > 50  # Ensure substantive answer
    
    @pytest.mark.asyncio
    async def test_synthesize_no_results(self, llm_synthesizer, mock_ollama_service):
        """Test synthesis with empty results."""
        mock_ollama_service.generate.return_value = {
            "response": "No data found for the requested ETF exposure analysis."
        }
        
        result = await llm_synthesizer.synthesize_answer(
            query="XYZ exposure to unknown company",
            intent="etf_exposure_to_company", 
            rows=[],
            entities=[]
        )
        
        assert "no data" in result.lower() or "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_synthesis_includes_numbers(self, llm_synthesizer, mock_ollama_service, sample_cypher_results):
        """Test that synthesis includes concrete numbers."""
        mock_ollama_service.generate.return_value = {
            "response": "The analysis shows SPY with 7.0% weight and QQQ with 8.0% weight in Apple Inc, totaling 367 million shares between both ETFs."
        }
        
        result = await llm_synthesizer.synthesize_answer(
            query="exposure analysis",
            intent="etf_exposure_to_company",
            rows=sample_cypher_results,
            entities=[]
        )
        
        # Should contain concrete numbers
        import re
        numbers = re.findall(r'\d+\.?\d*%?', result)
        assert len(numbers) > 0  # At least one number present


class TestGraphRAGPipeline:
    """Test complete GraphRAG pipeline."""
    
    @pytest.fixture
    def mock_pipeline_components(self):
        """Mock all pipeline components."""
        preprocessor = Mock()
        grounder = Mock()
        classifier = Mock()
        synthesizer = Mock()
        
        # Configure mocks
        preprocessor.preprocess = Mock(return_value={
            "normalized": "spy exposure to apple",
            "tokens": ["spy", "exposure", "apple"],
            "numbers": []
        })
        
        grounder.ground_entities = AsyncMock(return_value=[
            Entity(type="ETF", value="SPY", ticker="SPY"),
            Entity(type="Company", value="AAPL", symbol="AAPL")
        ])
        
        classifier.classify_intent = AsyncMock(return_value=Mock(
            intent_key="etf_exposure_to_company",
            confidence=0.85,
            grounded_entities=[
                Entity(type="ETF", value="SPY", ticker="SPY"),
                Entity(type="Company", value="AAPL", symbol="AAPL")
            ]
        ))
        
        synthesizer.synthesize_answer = AsyncMock(return_value="SPY has a 7.0% allocation to Apple Inc.")
        
        return preprocessor, grounder, classifier, synthesizer
    
    @pytest.fixture
    def pipeline(self, mock_pipeline_components, mock_neo4j_service):
        """Create pipeline with mocked components."""
        preprocessor, grounder, classifier, synthesizer = mock_pipeline_components
        
        pipeline = GraphRAGPipeline(mock_neo4j_service, Mock(), Mock())
        pipeline.preprocessor = preprocessor
        pipeline.entity_grounder = grounder
        pipeline.intent_classifier = classifier
        pipeline.llm_synthesizer = synthesizer
        
        return pipeline
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, pipeline, mock_neo4j_service, sample_cypher_results):
        """Test complete pipeline execution."""
        # Mock Cypher execution
        mock_neo4j_service.execute_read.return_value = sample_cypher_results
        
        with patch('app.graphrag.templates.cypher_queries.CYPHER_TEMPLATES') as mock_templates:
            mock_templates.__contains__ = Mock(return_value=True)
            mock_templates.__getitem__ = Mock(return_value=Mock(
                query="MATCH (e:ETF)-[h:HOLDS]->(c:Company) RETURN *",
                required_params=["ticker", "symbol"]
            ))
            
            result = await pipeline.process_query("SPY exposure to Apple")
        
        # Verify pipeline steps executed
        assert pipeline.preprocessor.preprocess.called
        assert pipeline.entity_grounder.ground_entities.called
        assert pipeline.intent_classifier.classify_intent.called
        assert pipeline.llm_synthesizer.synthesize_answer.called
        
        # Verify result structure
        assert "answer" in result
        assert "rows" in result
        assert "intent" in result
        assert "entities" in result
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_pipeline_missing_parameters(self, pipeline, mock_neo4j_service):
        """Test pipeline handling of missing parameters."""
        # Configure classifier to return missing params
        pipeline.intent_classifier.classify_intent.return_value = Mock(
            intent_key="etf_exposure_to_company",
            confidence=0.85,
            grounded_entities=[Entity(type="ETF", value="SPY", ticker="SPY")],
            missing_params=["symbol"]
        )
        
        with patch('app.graphrag.templates.cypher_queries.CYPHER_TEMPLATES') as mock_templates:
            mock_templates.__contains__ = Mock(return_value=True)
            mock_templates.__getitem__ = Mock(return_value=Mock(
                required_params=["ticker", "symbol"]
            ))
            
            result = await pipeline.process_query("SPY exposure")
        
        assert result["needs_parameters"] is True
        assert "symbol" in result["missing_params"]
    
    @pytest.mark.asyncio
    async def test_pipeline_unknown_intent(self, pipeline):
        """Test pipeline handling of unknown intent."""
        # Configure classifier to return unknown intent
        pipeline.intent_classifier.classify_intent.return_value = Mock(
            intent_key="unknown",
            confidence=0.2,
            grounded_entities=[]
        )
        
        result = await pipeline.process_query("unclear query")
        
        assert result["error"] is not None
        assert "unknown" in result["error"].lower() or "unclear" in result["error"].lower()