from fastapi import APIRouter, HTTPException, Depends
import structlog
from app.models.requests import IntentRequest
from app.models.responses import IntentResponse
from app.utils.validators import QueryValidator
from app.utils.security import security
from app.services.neo4j_service import Neo4jService
from app.services.ollama_service import OllamaService
from app.graphrag.preprocessor import Preprocessor
from app.graphrag.entity_grounder import EntityGrounder
from app.graphrag.intent_classifier import IntentClassifier
from app.graphrag.parameter_fulfiller import ParameterFulfiller

logger = structlog.get_logger()
router = APIRouter()

# Global service instances
neo4j_service = None
ollama_service = None
preprocessor = None
entity_grounder = None
intent_classifier = None
parameter_fulfiller = None

def get_services():
    """Dependency to get required services."""
    if any(service is None for service in [neo4j_service, ollama_service, preprocessor, entity_grounder, intent_classifier, parameter_fulfiller]):
        raise HTTPException(status_code=503, detail="Intent services not initialized")
    return {
        'preprocessor': preprocessor,
        'entity_grounder': entity_grounder,
        'intent_classifier': intent_classifier,
        'parameter_fulfiller': parameter_fulfiller
    }

@router.post("/", response_model=IntentResponse)
async def classify_intent(
    request: IntentRequest,
    services: dict = Depends(get_services)
):
    """
    Intent classification endpoint for debugging and development.
    Returns classified intent, confidence, grounded entities, and parameter requirements.
    
    This endpoint is useful for:
    - Debugging intent classification accuracy
    - Understanding entity grounding results
    - Checking parameter fulfillment before full query execution
    """
    try:
        # Validate and sanitize input
        sanitized_query = security.sanitize_user_input(request.query)
        validated_query = QueryValidator.validate_query_text(sanitized_query)
        
        logger.info("Processing intent classification",
                   original_length=len(request.query),
                   sanitized_length=len(validated_query))
        
        # Step 1: Preprocessing
        preprocessed = await services['preprocessor'].process(validated_query)
        
        # Step 2: Entity Grounding
        entities = await services['entity_grounder'].ground_entities(preprocessed)
        
        # Step 3: Intent Classification
        intent_result = await services['intent_classifier'].classify(validated_query, entities)
        
        # Step 4: Parameter Fulfillment (to check missing parameters)
        param_result = await services['parameter_fulfiller'].fulfill(intent_result, entities)
        
        # Prepare response
        response = IntentResponse(
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            entities=intent_result.entities,
            required_parameters=intent_result.required_parameters,
            missing_parameters=param_result.missing_parameters
        )
        
        logger.info("Intent classification completed",
                   intent=response.intent,
                   confidence=response.confidence,
                   entities_count=len(response.entities),
                   missing_params=len(response.missing_parameters))
        
        return response
        
    except ValueError as e:
        logger.warning("Intent classification validation failed", error=str(e), query=request.query[:100])
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error("Intent classification failed", error=str(e), query=request.query[:100])
        raise HTTPException(status_code=500, detail="Intent classification failed. Please try again.")

# Initialization function
def initialize_intent_router(neo4j: Neo4jService, ollama: OllamaService):
    """Initialize the intent router with service dependencies."""
    global neo4j_service, ollama_service, preprocessor, entity_grounder, intent_classifier, parameter_fulfiller
    
    neo4j_service = neo4j
    ollama_service = ollama
    preprocessor = Preprocessor()
    entity_grounder = EntityGrounder(neo4j)
    intent_classifier = IntentClassifier(ollama)
    parameter_fulfiller = ParameterFulfiller(neo4j)
    
    logger.info("Intent router initialized successfully")