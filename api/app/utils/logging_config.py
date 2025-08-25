import structlog
import logging
import sys
from typing import Any

def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = None) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

# ETF-specific logging utilities
def log_pipeline_step(logger, step_name: str, **kwargs) -> None:
    """Log a GraphRAG pipeline step with consistent format."""
    logger.info(f"Pipeline step: {step_name}", step=step_name, **kwargs)

def log_query_result(logger, intent: str, result_count: int, execution_time_ms: float, **kwargs) -> None:
    """Log query execution results with consistent format."""
    logger.info("Query executed",
               intent=intent,
               result_count=result_count,
               execution_time_ms=execution_time_ms,
               **kwargs)

def log_llm_interaction(logger, operation: str, model: str, prompt_length: int, response_length: int, **kwargs) -> None:
    """Log LLM interactions with consistent format."""
    logger.info("LLM interaction",
               operation=operation,
               model=model,
               prompt_length=prompt_length,
               response_length=response_length,
               **kwargs)