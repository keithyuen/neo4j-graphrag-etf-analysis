from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog
from contextlib import asynccontextmanager

from app.routers import ask, intent, graph, etl
from app.services.neo4j_service import Neo4jService
from app.services.ollama_service import OllamaService
from app.utils.logging_config import setup_logging
from app.models.responses import HealthResponse
from config import settings

# Setup logging
setup_logging(settings.log_level)
logger = structlog.get_logger()

# Global service instances
neo4j_service = None
ollama_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting ETF GraphRAG API")
    
    try:
        # Initialize services
        global neo4j_service, ollama_service
        
        logger.info("Initializing Neo4j service")
        neo4j_service = Neo4jService(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        
        logger.info("Initializing Ollama service")
        ollama_service = OllamaService(
            host=settings.ollama_host,
            model=settings.ollama_model
        )
        
        # Health check services
        neo4j_healthy = await neo4j_service.health_check()
        ollama_healthy = await ollama_service.health_check()
        
        if not neo4j_healthy:
            logger.error("Neo4j health check failed")
            raise Exception("Neo4j service not available")
        
        if not ollama_healthy:
            logger.warning("Ollama health check failed - LLM features may not work")
        
        # Initialize routers with services
        ask.initialize_ask_router(neo4j_service, ollama_service)
        intent.initialize_intent_router(neo4j_service, ollama_service)
        graph.initialize_graph_router(neo4j_service)
        
        logger.info("ETF GraphRAG API startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start ETF GraphRAG API", error=str(e))
        raise
    
    # Shutdown
    logger.info("Shutting down ETF GraphRAG API")
    
    if neo4j_service:
        neo4j_service.close()
    
    if ollama_service:
        await ollama_service.close()
    
    logger.info("ETF GraphRAG API shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="ETF GraphRAG API",
    description="ETF analysis with Neo4j GraphRAG and mandatory LLM synthesis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ask.router, prefix="/ask", tags=["GraphRAG"])
app.include_router(intent.router, prefix="/intent", tags=["Intent Classification"])
app.include_router(graph.router, prefix="/graph", tags=["Graph Visualization"])
app.include_router(etl.router, prefix="/etl", tags=["Data Management"])

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint that verifies all services are operational.
    """
    try:
        services = {
            "neo4j": False,
            "ollama": False
        }
        
        if neo4j_service:
            services["neo4j"] = await neo4j_service.health_check()
        
        if ollama_service:
            services["ollama"] = await ollama_service.health_check()
        
        # Determine overall status
        all_healthy = all(services.values())
        critical_healthy = services.get("neo4j", False)  # Neo4j is critical
        
        status = "healthy" if all_healthy else ("degraded" if critical_healthy else "unhealthy")
        
        return HealthResponse(
            status=status,
            version="1.0.0",
            services=services
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            services={"error": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ETF GraphRAG API",
        "version": "1.0.0",
        "description": "ETF analysis with Neo4j GraphRAG and mandatory LLM synthesis",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "ask": "/ask/",
            "intent": "/intent/",
            "graph": "/graph/subgraph",
            "etl": "/etl/refresh"
        },
        "features": [
            "7-step GraphRAG pipeline",
            "Mandatory LLM answer synthesis",
            "Pre-defined Cypher templates",
            "Security guardrails",
            "Interactive graph visualization",
            "ETF data management"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )