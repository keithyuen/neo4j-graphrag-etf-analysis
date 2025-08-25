from neo4j import GraphDatabase, Driver
from typing import Dict, List, Any, Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
import time

logger = structlog.get_logger()

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self._connect()
        
    def _connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Neo4j connection established", uri=self.uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e), uri=self.uri)
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a read-only Cypher query with parameters."""
        start_time = time.time()
        
        if not self.driver:
            self._connect()
            
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                rows = [self._serialize_record(record.data()) for record in result]
                
                execution_time = (time.time() - start_time) * 1000
                logger.info("Cypher query executed",
                           execution_time_ms=execution_time,
                           row_count=len(rows),
                           query=query[:100])
                
                return rows
        except Exception as e:
            logger.error("Cypher query failed", error=str(e), query=query[:100])
            raise
    
    def _serialize_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j objects to serializable dictionaries."""
        result = {}
        for key, value in data.items():
            result[key] = self._serialize_value(value)
        return result
    
    def _serialize_value(self, value: Any) -> Any:
        """Recursively serialize Neo4j values."""
        # Check for Neo4j DateTime specifically
        if hasattr(value, '__class__') and 'neo4j.time' in str(type(value)):
            return value.isoformat()
        
        # Check for Neo4j Node or Relationship objects  
        if hasattr(value, '_properties'):
            # Neo4j Node or Relationship object
            serialized = dict(value._properties)
            # Recursively serialize properties
            for k, v in serialized.items():
                serialized[k] = self._serialize_value(v)
            return serialized
            
        # Check for other datetime objects
        elif hasattr(value, 'isoformat'):
            return value.isoformat()
            
        # Handle collections
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
            
        # Handle basic types and unknown objects
        else:
            # Try to convert to JSON-serializable type
            try:
                import json
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                # If it can't be serialized, convert to string
                return str(value)
    
    async def execute_query_single(self, query: str, parameters: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single result."""
        results = await self.execute_query(query, parameters)
        return results[0] if results else None
    
    async def health_check(self) -> bool:
        """Check if Neo4j is accessible."""
        try:
            await self.execute_query("RETURN 1 as health")
            return True
        except Exception as e:
            logger.error("Neo4j health check failed", error=str(e))
            return False
    
    def close(self):
        """Close the driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
            
    def __del__(self):
        """Cleanup on destruction."""
        self.close()