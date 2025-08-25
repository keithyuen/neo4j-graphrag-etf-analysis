import re
import structlog
from typing import List, Set
from config import settings

logger = structlog.get_logger()

class SecurityGuards:
    """Security guardrails for the ETF GraphRAG system."""
    
    # Blocked patterns to prevent Cypher injection
    BLOCKED_PATTERNS = [
        r"(?i)(#cypher|; *match|drop|delete|create|merge|set|remove)",
        r"(?i)(call\s+apoc|call\s+db\.|admin|auth)",
        r"(?i)(load\s+csv|periodic\s+commit)",
        r"[<>{}()\\]",  # Potential script injection characters
        r"(?i)(javascript|script|eval|function)",  # Script injection
    ]
    
    ALLOWED_TICKERS: Set[str] = set(settings.allowed_tickers)
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern) for pattern in self.BLOCKED_PATTERNS]
    
    def sanitize_user_input(self, text: str) -> str:
        """Remove potentially dangerous patterns from user input."""
        if not text:
            return ""
        
        original_length = len(text)
        
        # Remove blocked patterns
        sanitized = text
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub("", sanitized)
        
        # Limit length
        sanitized = sanitized.strip()[:settings.max_query_length]
        
        if len(sanitized) != original_length:
            logger.warning("Input sanitized",
                          original_length=original_length,
                          sanitized_length=len(sanitized),
                          patterns_removed=original_length - len(sanitized))
        
        return sanitized
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate that ticker is in allowed list."""
        if not ticker:
            return False
        
        is_valid = ticker.upper() in self.ALLOWED_TICKERS
        
        if not is_valid:
            logger.warning("Invalid ticker attempted", 
                          ticker=ticker,
                          allowed_tickers=list(self.ALLOWED_TICKERS))
        
        return is_valid
    
    def validate_multiple_tickers(self, tickers: List[str]) -> List[str]:
        """Validate multiple tickers and return only valid ones."""
        valid_tickers = []
        
        for ticker in tickers:
            if self.validate_ticker(ticker):
                valid_tickers.append(ticker.upper())
        
        return valid_tickers
    
    def validate_cypher_template(self, template: str) -> bool:
        """Ensure Cypher template is read-only with LIMIT."""
        if not template:
            return False
        
        upper_template = template.upper()
        
        # Must have LIMIT clause
        has_limit = "LIMIT" in upper_template
        
        # Must be read-only (no write operations)
        write_operations = ["CREATE", "DELETE", "SET", "MERGE", "DROP", "REMOVE"]
        is_read_only = not any(op in upper_template for op in write_operations)
        
        # Check for dangerous functions
        dangerous_functions = [
            "CALL APOC", "CALL DB.", "LOAD CSV", "PERIODIC COMMIT",
            "CALL { CREATE", "CALL { MERGE", "CALL { DELETE"
        ]
        has_dangerous_functions = any(func in upper_template for func in dangerous_functions)
        
        is_valid = has_limit and is_read_only and not has_dangerous_functions
        
        if not is_valid:
            logger.error("Invalid Cypher template",
                        has_limit=has_limit,
                        is_read_only=is_read_only,
                        has_dangerous_functions=has_dangerous_functions,
                        template=template[:200])
        
        return is_valid
    
    def validate_parameters(self, parameters: dict) -> dict:
        """Validate and sanitize query parameters."""
        sanitized = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Sanitize string parameters
                sanitized_value = self.sanitize_user_input(value)
                
                # Special validation for ticker parameters
                if "ticker" in key.lower() and not self.validate_ticker(sanitized_value):
                    logger.warning("Invalid ticker in parameters", key=key, value=value)
                    continue
                
                sanitized[key] = sanitized_value
                
            elif isinstance(value, (int, float)):
                # Validate numeric parameters
                if key == "top_n":
                    # Limit top_n to maximum for security
                    sanitized[key] = min(max(int(value), 1), settings.max_cypher_limit)
                elif key == "threshold":
                    # Ensure threshold is between 0 and 1
                    sanitized[key] = max(0.0, min(float(value), 1.0))
                else:
                    sanitized[key] = value
            else:
                # Pass through other types (bool, None, etc.)
                sanitized[key] = value
        
        return sanitized
    
    def check_rate_limit(self, user_id: str = None) -> bool:
        """Basic rate limiting check (placeholder for future implementation)."""
        # TODO: Implement actual rate limiting with Redis or in-memory store
        return True
    
    def log_security_event(self, event_type: str, details: dict) -> None:
        """Log security-related events for monitoring."""
        logger.warning("Security event",
                      event_type=event_type,
                      **details)

# Global security instance
security = SecurityGuards()