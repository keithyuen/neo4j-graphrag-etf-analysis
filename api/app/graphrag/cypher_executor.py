import structlog
import time
from typing import Dict, Any
from app.models.entities import CypherResult
from app.services.neo4j_service import Neo4jService
from app.graphrag.templates.cypher_queries import get_template

logger = structlog.get_logger()

class CypherExecutor:
    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j = neo4j_service
    
    async def execute(self, intent: str, parameters: Dict[str, Any]) -> CypherResult:
        """
        Execute pre-defined Cypher query for the given intent with parameters.
        Enforces security guardrails: read-only, LIMIT enforcement, parameter validation.
        """
        start_time = time.time()
        
        try:
            # Get the pre-defined template
            template = get_template(intent)
            
            # Validate template security
            self._validate_template_security(template)
            
            # Validate parameters
            missing_params = template.validate_params(parameters)
            if missing_params:
                raise ValueError(f"Missing required parameters: {missing_params}")
            
            # Log query execution
            logger.info("Executing Cypher query",
                       intent=intent,
                       parameters=list(parameters.keys()))
            
            # Execute the query
            rows = await self.neo4j.execute_query(template.query, parameters)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Count nodes and edges in results if it's a subgraph query
            node_count, edge_count = self._count_graph_elements(rows, intent)
            
            result = CypherResult(
                query=template.query.strip(),
                parameters=parameters,
                rows=rows,
                execution_time_ms=execution_time_ms,
                node_count=node_count,
                edge_count=edge_count
            )
            
            logger.info("Cypher execution completed",
                       intent=intent,
                       execution_time_ms=execution_time_ms,
                       row_count=len(rows),
                       node_count=node_count,
                       edge_count=edge_count)
            
            return result
            
        except Exception as e:
            logger.error("Cypher execution failed",
                        intent=intent,
                        error=str(e),
                        parameters=parameters)
            raise
    
    def _validate_template_security(self, template) -> None:
        """Validate that the template meets security requirements."""
        if not template.has_limit():
            raise SecurityError("Query must have LIMIT clause")
        
        if not template.is_read_only():
            raise SecurityError("Only read-only queries are allowed")
        
        # Additional security checks
        query_upper = template.query.upper()
        
        # Check for dangerous functions
        dangerous_patterns = [
            "CALL APOC", "CALL DB.", "LOAD CSV", "PERIODIC COMMIT",
            "CALL { CREATE", "CALL { MERGE", "CALL { DELETE"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                raise SecurityError(f"Dangerous pattern detected: {pattern}")
    
    def _count_graph_elements(self, rows: list, intent: str) -> tuple:
        """Count nodes and edges in query results for graph visualizations."""
        if intent != "top_holdings_subgraph" or not rows:
            return None, None
        
        # For subgraph queries, count unique nodes and edges
        nodes = set()
        edges = 0
        
        for row in rows:
            # Count nodes (ETF, Company, Sector)
            if 'e' in row:  # ETF node
                nodes.add(f"ETF:{row['e'].get('ticker', '')}")
            if 'c' in row:  # Company node
                nodes.add(f"Company:{row['c'].get('symbol', '')}")
            if 's' in row:  # Sector node
                nodes.add(f"Sector:{row['s'].get('name', '')}")
            
            # Count relationships
            if 'h' in row:  # HOLDS relationship
                edges += 1
            # IN_SECTOR relationships are implied by company-sector pairs
        
        return len(nodes), edges

class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass