from fastapi import APIRouter, HTTPException, Depends
import structlog
from app.models.requests import AskRequest
from app.models.responses import GraphRAGResponse
from app.utils.validators import QueryValidator
from app.utils.security import security
from app.services.neo4j_service import Neo4jService
from app.services.ollama_service import OllamaService
from app.graphrag.pipeline import GraphRAGPipeline
from config import settings

logger = structlog.get_logger()
router = APIRouter()

# Global service instances (will be initialized in main.py)
neo4j_service = None
ollama_service = None
pipeline = None

def get_pipeline() -> GraphRAGPipeline:
    """Dependency to get GraphRAG pipeline instance."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="GraphRAG pipeline not initialized")
    return pipeline

@router.post("/", response_model=GraphRAGResponse)
async def ask_query(
    request: AskRequest,
    graphrag_pipeline: GraphRAGPipeline = Depends(get_pipeline)
):
    """
    Main GraphRAG endpoint with mandatory LLM synthesis.
    Processes user query through complete 7-step pipeline.
    
    Steps:
    1. Text preprocessing and normalization
    2. Entity grounding via Neo4j
    3. Intent classification via LLM
    4. Parameter fulfillment and validation
    5. Cypher execution with guardrails
    6. LLM answer synthesis (MANDATORY)
    7. Response assembly with metadata
    """
    try:
        # Validate and sanitize input
        sanitized_query = security.sanitize_user_input(request.query)
        validated_query = QueryValidator.validate_query_text(sanitized_query)
        
        logger.info("Processing ask query",
                   original_length=len(request.query),
                   sanitized_length=len(validated_query))
        
        # Execute complete GraphRAG pipeline
        result = await graphrag_pipeline.process_query(validated_query)
        
        # Log successful completion
        logger.info("Ask query completed successfully",
                   intent=result.intent,
                   result_count=len(result.rows),
                   total_time=result.metadata.timing.get('total_pipeline', 0),
                   has_llm_answer=bool(result.answer))
        
        return result
        
    except ValueError as e:
        logger.warning("Ask query validation failed", error=str(e), query=request.query[:100])
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error("Ask query processing failed", error=str(e), query=request.query[:100])
        raise HTTPException(status_code=500, detail="Query processing failed. Please try again.")

# Initialization function to be called from main.py
def initialize_ask_router(neo4j: Neo4jService, ollama: OllamaService):
    """Initialize the ask router with service dependencies."""
    global neo4j_service, ollama_service, pipeline
    neo4j_service = neo4j
    ollama_service = ollama
    pipeline = GraphRAGPipeline(neo4j, ollama)
    logger.info("Ask router initialized successfully")