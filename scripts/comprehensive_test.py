#!/usr/bin/env python3
"""
Comprehensive Testing Script for ETF GraphRAG System

This script validates all system components:
1. Database Layer Tests (Neo4j connectivity, schema, data integrity)
2. API Layer Tests (endpoints, GraphRAG pipeline, error handling)
3. UI Layer Tests (accessibility, basic functionality)
4. Integration Tests (full pipeline, performance)

Usage:
    python comprehensive_test.py [--no-integration] [--report-format json|text]
"""

import sys
import asyncio
import time
import json
import argparse
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import platform

# Test dependencies
import httpx
import neo4j
from neo4j import AsyncGraphDatabase
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result container."""
    name: str
    category: str
    status: str  # "PASS", "FAIL", "SKIP", "WARN"
    duration_ms: float
    details: Optional[str] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


@dataclass
class TestReport:
    """Comprehensive test report."""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    warnings: int
    total_duration_ms: float
    system_info: Dict[str, Any]
    results: List[TestResult]
    summary: Dict[str, Any]


class ComprehensiveTestSuite:
    """Main test suite class."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
        # Configuration
        self.config = {
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_user': 'neo4j',
            'neo4j_password': 'password123',
            'api_base_url': 'http://localhost:8000',
            'ui_base_url': 'http://localhost:3000',
            'ollama_base_url': 'http://localhost:11434',
            'allowed_tickers': ['SPY', 'QQQ', 'IWM', 'IJH', 'IVE', 'IVW'],
            'test_timeout': 30.0,
            'performance_thresholds': {
                'api_response_time_ms': 2000,
                'database_query_time_ms': 1000,
                'ui_load_time_ms': 5000
            }
        }
        
        # Test data
        self.test_queries = [
            "What is SPY's exposure to Apple?",
            "Show QQQ sector allocation",
            "Compare IWM and IJH overlapping holdings",
            "Which ETFs hold Microsoft?",
            "Technology sector exposure across all ETFs"
        ]
        
        self.test_intents = [
            "etf_exposure_to_company",
            "etf_sector_allocation", 
            "etf_overlap_analysis",
            "company_etf_holders",
            "sector_exposure_analysis"
        ]

    async def run_all_tests(self, skip_integration: bool = False) -> TestReport:
        """Run all test categories."""
        logger.info("🚀 Starting Comprehensive ETF GraphRAG System Tests")
        
        # System info
        system_info = self._get_system_info()
        logger.info(f"System: {system_info['platform']} {system_info['version']}")
        logger.info(f"Python: {system_info['python_version']}")
        logger.info(f"Memory: {system_info['memory_gb']:.1f}GB")
        logger.info(f"CPU: {system_info['cpu_count']} cores")
        
        # Run test categories
        await self._run_database_tests()
        await self._run_api_tests()
        await self._run_ui_tests()
        
        if not skip_integration:
            await self._run_integration_tests()
        else:
            logger.info("⏭️  Skipping integration tests")
        
        # Generate report
        return self._generate_report(system_info)

    async def _run_database_tests(self):
        """Test Neo4j database layer."""
        logger.info("\n📊 Running Database Layer Tests")
        
        # Test 1: Neo4j Connectivity
        await self._test_neo4j_connectivity()
        
        # Test 2: Schema Validation
        await self._test_schema_validation()
        
        # Test 3: Data Integrity
        await self._test_data_integrity()
        
        # Test 4: Relationship Validation
        await self._test_relationship_validation()
        
        # Test 5: Query Performance
        await self._test_query_performance()

    async def _test_neo4j_connectivity(self):
        """Test Neo4j database connectivity."""
        start_time = time.time()
        
        try:
            driver = AsyncGraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=(self.config['neo4j_user'], self.config['neo4j_password'])
            )
            
            async with driver.session() as session:
                result = await session.run("RETURN 'Neo4j Connected' as message")
                record = await result.single()
                
                if record and record['message'] == 'Neo4j Connected':
                    await driver.close()
                    self._add_result(TestResult(
                        name="Neo4j Connectivity",
                        category="Database",
                        status="PASS",
                        duration_ms=(time.time() - start_time) * 1000,
                        details="Successfully connected to Neo4j"
                    ))
                else:
                    raise Exception("Unexpected response from Neo4j")
                    
        except Exception as e:
            self._add_result(TestResult(
                name="Neo4j Connectivity",
                category="Database", 
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_schema_validation(self):
        """Test database schema validation."""
        start_time = time.time()
        
        try:
            driver = AsyncGraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=(self.config['neo4j_user'], self.config['neo4j_password'])
            )
            
            async with driver.session() as session:
                # Check node labels
                result = await session.run("CALL db.labels()")
                labels = [record['label'] async for record in result]
                expected_labels = ['ETF', 'Company', 'Sector', 'Intent', 'Entity', 'Term']
                
                missing_labels = set(expected_labels) - set(labels)
                if missing_labels:
                    raise Exception(f"Missing node labels: {missing_labels}")
                
                # Check relationship types
                result = await session.run("CALL db.relationshipTypes()")
                rel_types = [record['relationshipType'] async for record in result]
                expected_rels = ['HOLDS', 'IN_SECTOR', 'REQUIRES', 'MAPS_TO']
                
                missing_rels = set(expected_rels) - set(rel_types)
                if missing_rels:
                    raise Exception(f"Missing relationship types: {missing_rels}")
                
                # Check constraints
                result = await session.run("SHOW CONSTRAINTS")
                constraints = [record async for record in result]
                
                await driver.close()
                
                self._add_result(TestResult(
                    name="Schema Validation",
                    category="Database",
                    status="PASS",
                    duration_ms=(time.time() - start_time) * 1000,
                    details=f"Found {len(labels)} labels, {len(rel_types)} relationship types, {len(constraints)} constraints",
                    metrics={
                        'labels_count': len(labels),
                        'relationship_types_count': len(rel_types),
                        'constraints_count': len(constraints)
                    }
                ))
                
        except Exception as e:
            self._add_result(TestResult(
                name="Schema Validation",
                category="Database",
                status="FAIL", 
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_data_integrity(self):
        """Test data integrity checks."""
        start_time = time.time()
        
        try:
            driver = AsyncGraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=(self.config['neo4j_user'], self.config['neo4j_password'])
            )
            
            issues = []
            metrics = {}
            
            async with driver.session() as session:
                # Check ETF nodes
                result = await session.run("MATCH (e:ETF) RETURN count(e) as count")
                etf_count = (await result.single())['count']
                metrics['etf_count'] = etf_count
                
                if etf_count == 0:
                    issues.append("No ETF nodes found")
                
                # Check Company nodes  
                result = await session.run("MATCH (c:Company) RETURN count(c) as count")
                company_count = (await result.single())['count']
                metrics['company_count'] = company_count
                
                if company_count == 0:
                    issues.append("No Company nodes found")
                
                # Check Sector nodes
                result = await session.run("MATCH (s:Sector) RETURN count(s) as count")
                sector_count = (await result.single())['count']
                metrics['sector_count'] = sector_count
                
                if sector_count == 0:
                    issues.append("No Sector nodes found")
                
                # Check for orphaned nodes
                result = await session.run("""
                    MATCH (c:Company) 
                    WHERE NOT (c)-[:IN_SECTOR]->(:Sector) 
                    RETURN count(c) as orphaned_companies
                """)
                orphaned_companies = (await result.single())['orphaned_companies']
                metrics['orphaned_companies'] = orphaned_companies
                
                if orphaned_companies > 0:
                    issues.append(f"{orphaned_companies} companies without sector assignments")
                
                # Check weight constraints
                result = await session.run("""
                    MATCH (:ETF)-[h:HOLDS]->(:Company)
                    WHERE h.weight < 0 OR h.weight > 1
                    RETURN count(h) as invalid_weights
                """)
                invalid_weights = (await result.single())['invalid_weights']
                metrics['invalid_weights'] = invalid_weights
                
                if invalid_weights > 0:
                    issues.append(f"{invalid_weights} holdings with invalid weights")
                
            await driver.close()
            
            status = "FAIL" if issues else "PASS"
            details = f"Data integrity check: {len(issues)} issues found" if issues else "All data integrity checks passed"
            
            self._add_result(TestResult(
                name="Data Integrity",
                category="Database",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                error="; ".join(issues) if issues else None,
                metrics=metrics
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Data Integrity",
                category="Database",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_relationship_validation(self):
        """Test relationship validation."""
        start_time = time.time()
        
        try:
            driver = AsyncGraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=(self.config['neo4j_user'], self.config['neo4j_password'])
            )
            
            issues = []
            metrics = {}
            
            async with driver.session() as session:
                # Check HOLDS relationships
                result = await session.run("MATCH (:ETF)-[h:HOLDS]->(:Company) RETURN count(h) as count")
                holds_count = (await result.single())['count']
                metrics['holds_relationships'] = holds_count
                
                if holds_count == 0:
                    issues.append("No HOLDS relationships found")
                
                # Check IN_SECTOR relationships
                result = await session.run("MATCH (:Company)-[s:IN_SECTOR]->(:Sector) RETURN count(s) as count")
                sector_rels = (await result.single())['count']
                metrics['in_sector_relationships'] = sector_rels
                
                if sector_rels == 0:
                    issues.append("No IN_SECTOR relationships found")
                
                # Check for duplicate relationships
                result = await session.run("""
                    MATCH (e:ETF)-[h:HOLDS]->(c:Company)
                    WITH e, c, count(h) as rel_count
                    WHERE rel_count > 1
                    RETURN count(*) as duplicates
                """)
                duplicates = (await result.single())['duplicates']
                metrics['duplicate_holds'] = duplicates
                
                if duplicates > 0:
                    issues.append(f"{duplicates} duplicate HOLDS relationships")
                
                # Validate ETF ticker constraints
                for ticker in self.config['allowed_tickers']:
                    result = await session.run(
                        "MATCH (e:ETF {ticker: $ticker}) RETURN count(e) as count",
                        ticker=ticker
                    )
                    count = (await result.single())['count']
                    if count == 0:
                        issues.append(f"Missing ETF: {ticker}")
                    elif count > 1:
                        issues.append(f"Duplicate ETF: {ticker}")
                
            await driver.close()
            
            status = "FAIL" if issues else "PASS"
            details = f"Relationship validation: {len(issues)} issues found" if issues else "All relationship validations passed"
            
            self._add_result(TestResult(
                name="Relationship Validation",
                category="Database",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                error="; ".join(issues) if issues else None,
                metrics=metrics
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Relationship Validation",
                category="Database",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_query_performance(self):
        """Test database query performance."""
        start_time = time.time()
        
        try:
            driver = AsyncGraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=(self.config['neo4j_user'], self.config['neo4j_password'])
            )
            
            performance_metrics = {}
            
            async with driver.session() as session:
                # Test 1: Simple ETF lookup
                query_start = time.time()
                result = await session.run("MATCH (e:ETF {ticker: 'SPY'}) RETURN e")
                await result.consume()
                simple_query_time = (time.time() - query_start) * 1000
                performance_metrics['simple_query_ms'] = simple_query_time
                
                # Test 2: Complex holdings query
                query_start = time.time()
                result = await session.run("""
                    MATCH (e:ETF {ticker: 'SPY'})-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
                    RETURN e.ticker, c.symbol, c.name, s.name, h.weight
                    ORDER BY h.weight DESC
                    LIMIT 10
                """)
                await result.consume()
                complex_query_time = (time.time() - query_start) * 1000
                performance_metrics['complex_query_ms'] = complex_query_time
                
                # Test 3: Aggregation query
                query_start = time.time()
                result = await session.run("""
                    MATCH (e:ETF)-[h:HOLDS]->(c:Company)-[:IN_SECTOR]->(s:Sector)
                    RETURN s.name, sum(h.weight) as total_weight, count(c) as company_count
                    ORDER BY total_weight DESC
                """)
                await result.consume()
                aggregation_query_time = (time.time() - query_start) * 1000
                performance_metrics['aggregation_query_ms'] = aggregation_query_time
                
            await driver.close()
            
            # Check against thresholds
            threshold = self.config['performance_thresholds']['database_query_time_ms']
            slow_queries = [k for k, v in performance_metrics.items() if v > threshold]
            
            status = "WARN" if slow_queries else "PASS"
            details = f"All queries under {threshold}ms threshold" if not slow_queries else f"Slow queries: {slow_queries}"
            
            self._add_result(TestResult(
                name="Query Performance",
                category="Database",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics=performance_metrics
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Query Performance",
                category="Database",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _run_api_tests(self):
        """Test API layer."""
        logger.info("\n🔌 Running API Layer Tests")
        
        # Test 1: Health Check
        await self._test_api_health()
        
        # Test 2: Authentication/Security
        await self._test_api_security()
        
        # Test 3: Ask Endpoint
        await self._test_ask_endpoint()
        
        # Test 4: Intent Endpoint
        await self._test_intent_endpoint()
        
        # Test 5: Graph Endpoint
        await self._test_graph_endpoint()
        
        # Test 6: ETL Endpoints
        await self._test_etl_endpoints()
        
        # Test 7: Error Handling
        await self._test_api_error_handling()
        
        # Test 8: Performance
        await self._test_api_performance()

    async def _test_api_health(self):
        """Test API health endpoint."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                response = await client.get(f"{self.config['api_base_url']}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    self._add_result(TestResult(
                        name="API Health Check",
                        category="API",
                        status="PASS",
                        duration_ms=(time.time() - start_time) * 1000,
                        details=f"API healthy: {health_data.get('status', 'unknown')}",
                        metrics={'status_code': response.status_code, 'response_time_ms': response.elapsed.total_seconds() * 1000}
                    ))
                else:
                    raise Exception(f"Health check failed with status {response.status_code}")
                    
        except Exception as e:
            self._add_result(TestResult(
                name="API Health Check",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_api_security(self):
        """Test API security measures."""
        start_time = time.time()
        
        try:
            security_issues = []
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                # Test 1: SQL Injection attempt
                malicious_query = "'; DROP TABLE users; --"
                response = await client.post(
                    f"{self.config['api_base_url']}/ask",
                    json={"query": malicious_query}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "DROP" in result.get("answer", ""):
                        security_issues.append("Potential SQL injection vulnerability")
                
                # Test 2: XSS attempt
                xss_query = "<script>alert('xss')</script>"
                response = await client.post(
                    f"{self.config['api_base_url']}/ask",
                    json={"query": xss_query}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "<script>" in result.get("answer", ""):
                        security_issues.append("Potential XSS vulnerability")
                
                # Test 3: Large payload
                large_query = "A" * 10000
                response = await client.post(
                    f"{self.config['api_base_url']}/ask",
                    json={"query": large_query}
                )
                
                if response.status_code != 413 and response.status_code != 400:
                    security_issues.append("No payload size limit enforcement")
                
                # Test 4: Rate limiting (basic check)
                responses = []
                for i in range(5):
                    resp = await client.post(
                        f"{self.config['api_base_url']}/ask",
                        json={"query": f"test query {i}"}
                    )
                    responses.append(resp.status_code)
                
                if all(status == 200 for status in responses):
                    # This is not necessarily a security issue, just noting
                    pass
            
            status = "FAIL" if security_issues else "PASS"
            details = f"Security tests passed" if not security_issues else f"Issues: {security_issues}"
            
            self._add_result(TestResult(
                name="API Security",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                error="; ".join(security_issues) if security_issues else None
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="API Security",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_ask_endpoint(self):
        """Test /ask endpoint functionality."""
        start_time = time.time()
        
        try:
            successful_queries = 0
            total_queries = len(self.test_queries)
            query_times = []
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                for query in self.test_queries:
                    query_start = time.time()
                    
                    response = await client.post(
                        f"{self.config['api_base_url']}/ask",
                        json={"query": query}
                    )
                    
                    query_time = (time.time() - query_start) * 1000
                    query_times.append(query_time)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Validate response structure
                        required_fields = ['answer', 'rows', 'intent', 'entities', 'metadata']
                        if all(field in result for field in required_fields):
                            # Validate LLM answer is present
                            if result['answer'] and len(result['answer']) > 10:
                                successful_queries += 1
                    
            avg_query_time = sum(query_times) / len(query_times) if query_times else 0
            success_rate = successful_queries / total_queries if total_queries > 0 else 0
            
            status = "PASS" if success_rate >= 0.8 else "FAIL"
            details = f"Success rate: {success_rate:.1%} ({successful_queries}/{total_queries})"
            
            self._add_result(TestResult(
                name="Ask Endpoint",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'success_rate': success_rate,
                    'avg_query_time_ms': avg_query_time,
                    'successful_queries': successful_queries,
                    'total_queries': total_queries
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Ask Endpoint",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_intent_endpoint(self):
        """Test /intent endpoint functionality."""
        start_time = time.time()
        
        try:
            successful_classifications = 0
            total_queries = len(self.test_queries)
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                for query in self.test_queries:
                    response = await client.post(
                        f"{self.config['api_base_url']}/intent",
                        json={"query": query}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Validate response structure
                        required_fields = ['intent_key', 'confidence', 'grounded_entities']
                        if all(field in result for field in required_fields):
                            # Check if intent is recognized
                            if result['intent_key'] in self.test_intents or result['confidence'] > 0.5:
                                successful_classifications += 1
            
            success_rate = successful_classifications / total_queries if total_queries > 0 else 0
            
            status = "PASS" if success_rate >= 0.7 else "FAIL"
            details = f"Intent classification success rate: {success_rate:.1%}"
            
            self._add_result(TestResult(
                name="Intent Endpoint",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'success_rate': success_rate,
                    'successful_classifications': successful_classifications,
                    'total_queries': total_queries
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Intent Endpoint",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_graph_endpoint(self):
        """Test /graph/subgraph endpoint."""
        start_time = time.time()
        
        try:
            successful_subgraphs = 0
            total_tickers = len(self.config['allowed_tickers'])
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                for ticker in self.config['allowed_tickers']:
                    response = await client.get(
                        f"{self.config['api_base_url']}/graph/subgraph",
                        params={"ticker": ticker, "top": 10}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Validate subgraph structure
                        if 'nodes' in result and 'edges' in result:
                            if len(result['nodes']) > 0 and len(result['edges']) > 0:
                                successful_subgraphs += 1
            
            success_rate = successful_subgraphs / total_tickers if total_tickers > 0 else 0
            
            status = "PASS" if success_rate >= 0.8 else "FAIL"
            details = f"Subgraph generation success rate: {success_rate:.1%}"
            
            self._add_result(TestResult(
                name="Graph Endpoint",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'success_rate': success_rate,
                    'successful_subgraphs': successful_subgraphs,
                    'total_tickers': total_tickers
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Graph Endpoint",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_etl_endpoints(self):
        """Test ETL endpoints."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for ETL
                # Test cache stats endpoint
                response = await client.get(f"{self.config['api_base_url']}/cache/stats")
                
                cache_stats_working = response.status_code == 200
                
                # Test ETL refresh (non-destructive)
                response = await client.post(
                    f"{self.config['api_base_url']}/etl/refresh",
                    json={"tickers": ["SPY"]}  # Test with just one ticker
                )
                
                etl_refresh_working = response.status_code in [200, 202]  # Accept async processing
                
            status = "PASS" if cache_stats_working and etl_refresh_working else "WARN"
            details = f"Cache stats: {'✓' if cache_stats_working else '✗'}, ETL refresh: {'✓' if etl_refresh_working else '✗'}"
            
            self._add_result(TestResult(
                name="ETL Endpoints",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'cache_stats_working': cache_stats_working,
                    'etl_refresh_working': etl_refresh_working
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="ETL Endpoints",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_api_error_handling(self):
        """Test API error handling."""
        start_time = time.time()
        
        try:
            error_tests = []
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                # Test 1: Invalid JSON
                try:
                    response = await client.post(
                        f"{self.config['api_base_url']}/ask",
                        content="invalid json",
                        headers={"Content-Type": "application/json"}
                    )
                    error_tests.append(("Invalid JSON", response.status_code in [400, 422]))
                except:
                    error_tests.append(("Invalid JSON", True))  # Exception is acceptable
                
                # Test 2: Missing required fields
                response = await client.post(
                    f"{self.config['api_base_url']}/ask",
                    json={}
                )
                error_tests.append(("Missing fields", response.status_code in [400, 422]))
                
                # Test 3: Invalid ticker
                response = await client.get(
                    f"{self.config['api_base_url']}/graph/subgraph",
                    params={"ticker": "INVALID", "top": 10}
                )
                error_tests.append(("Invalid ticker", response.status_code in [400, 422]))
                
                # Test 4: Non-existent endpoint
                response = await client.get(f"{self.config['api_base_url']}/nonexistent")
                error_tests.append(("Non-existent endpoint", response.status_code == 404))
            
            passed_tests = sum(1 for _, passed in error_tests if passed)
            total_tests = len(error_tests)
            
            status = "PASS" if passed_tests == total_tests else "WARN"
            details = f"Error handling tests: {passed_tests}/{total_tests} passed"
            
            self._add_result(TestResult(
                name="API Error Handling",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={'passed_error_tests': passed_tests, 'total_error_tests': total_tests}
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="API Error Handling",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_api_performance(self):
        """Test API performance."""
        start_time = time.time()
        
        try:
            response_times = []
            threshold = self.config['performance_thresholds']['api_response_time_ms']
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                # Test multiple requests
                for i in range(5):
                    request_start = time.time()
                    response = await client.post(
                        f"{self.config['api_base_url']}/ask",
                        json={"query": "What is SPY?"}
                    )
                    request_time = (time.time() - request_start) * 1000
                    response_times.append(request_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else float('inf')
            max_response_time = max(response_times) if response_times else float('inf')
            
            status = "PASS" if avg_response_time < threshold else "WARN"
            details = f"Avg response time: {avg_response_time:.0f}ms (threshold: {threshold}ms)"
            
            self._add_result(TestResult(
                name="API Performance",
                category="API",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'avg_response_time_ms': avg_response_time,
                    'max_response_time_ms': max_response_time,
                    'threshold_ms': threshold
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="API Performance",
                category="API",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _run_ui_tests(self):
        """Test UI layer."""
        logger.info("\n🎨 Running UI Layer Tests")
        
        # Test 1: UI Accessibility
        await self._test_ui_accessibility()
        
        # Test 2: API Integration
        await self._test_ui_api_integration()
        
        # Test 3: Basic Functionality
        await self._test_ui_functionality()

    async def _test_ui_accessibility(self):
        """Test UI accessibility and loading."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                response = await client.get(self.config['ui_base_url'])
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Basic HTML structure checks
                    has_title = '<title>' in content
                    has_meta_viewport = 'viewport' in content
                    has_body = '<body' in content
                    
                    # Check for React app mount point
                    has_app_root = 'id="root"' in content or 'id="app"' in content
                    
                    accessibility_score = sum([has_title, has_meta_viewport, has_body, has_app_root])
                    
                    status = "PASS" if accessibility_score >= 3 else "WARN"
                    details = f"UI accessibility score: {accessibility_score}/4"
                    
                    self._add_result(TestResult(
                        name="UI Accessibility",
                        category="UI",
                        status=status,
                        duration_ms=(time.time() - start_time) * 1000,
                        details=details,
                        metrics={
                            'accessibility_score': accessibility_score,
                            'has_title': has_title,
                            'has_viewport': has_meta_viewport,
                            'has_body': has_body,
                            'has_app_root': has_app_root
                        }
                    ))
                else:
                    raise Exception(f"UI not accessible, status code: {response.status_code}")
                    
        except Exception as e:
            self._add_result(TestResult(
                name="UI Accessibility",
                category="UI",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_ui_api_integration(self):
        """Test UI-API integration."""
        start_time = time.time()
        
        try:
            # Check if UI can reach API
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                # Test if UI serves static assets
                response = await client.get(f"{self.config['ui_base_url']}/")
                ui_accessible = response.status_code == 200
                
                # Test if API is reachable from UI context
                # This is a basic check - real integration would require browser automation
                api_response = await client.get(f"{self.config['api_base_url']}/health")
                api_accessible = api_response.status_code == 200
                
            status = "PASS" if ui_accessible and api_accessible else "FAIL"
            details = f"UI accessible: {'✓' if ui_accessible else '✗'}, API accessible: {'✓' if api_accessible else '✗'}"
            
            self._add_result(TestResult(
                name="UI-API Integration",
                category="UI",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'ui_accessible': ui_accessible,
                    'api_accessible': api_accessible
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="UI-API Integration",
                category="UI",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_ui_functionality(self):
        """Test basic UI functionality."""
        start_time = time.time()
        
        try:
            # This is a placeholder for more sophisticated UI testing
            # In a real scenario, you'd use tools like Playwright or Selenium
            
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                # Check if main routes are accessible
                routes_to_test = ['/', '/graph']
                accessible_routes = 0
                
                for route in routes_to_test:
                    try:
                        response = await client.get(f"{self.config['ui_base_url']}{route}")
                        if response.status_code == 200:
                            accessible_routes += 1
                    except:
                        pass
                
                # Check for common UI components in HTML
                response = await client.get(self.config['ui_base_url'])
                if response.status_code == 200:
                    content = response.text.lower()
                    
                    # Look for evidence of key UI components
                    has_query_form = 'query' in content or 'search' in content
                    has_graph_elements = 'graph' in content or 'cytoscape' in content
                    has_navigation = 'nav' in content or 'menu' in content
                    
                    functionality_score = accessible_routes + sum([has_query_form, has_graph_elements, has_navigation])
                    max_score = len(routes_to_test) + 3
                    
                    status = "PASS" if functionality_score >= max_score * 0.7 else "WARN"
                    details = f"UI functionality score: {functionality_score}/{max_score}"
                    
                    self._add_result(TestResult(
                        name="UI Functionality",
                        category="UI",
                        status=status,
                        duration_ms=(time.time() - start_time) * 1000,
                        details=details,
                        metrics={
                            'functionality_score': functionality_score,
                            'accessible_routes': accessible_routes,
                            'total_routes': len(routes_to_test)
                        }
                    ))
                else:
                    raise Exception("UI not accessible for functionality testing")
                    
        except Exception as e:
            self._add_result(TestResult(
                name="UI Functionality",
                category="UI",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _run_integration_tests(self):
        """Run full integration tests."""
        logger.info("\n🔄 Running Integration Tests")
        
        # Test 1: Full GraphRAG Pipeline
        await self._test_full_pipeline()
        
        # Test 2: Data Flow Validation
        await self._test_data_flow()
        
        # Test 3: Load Testing
        await self._test_load_performance()

    async def _test_full_pipeline(self):
        """Test full GraphRAG pipeline end-to-end."""
        start_time = time.time()
        
        try:
            pipeline_steps = []
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                query = "What is SPY's exposure to Apple Inc?"
                
                # Step 1: Intent classification
                intent_response = await client.post(
                    f"{self.config['api_base_url']}/intent",
                    json={"query": query}
                )
                pipeline_steps.append(("Intent Classification", intent_response.status_code == 200))
                
                # Step 2: Full ask pipeline
                ask_response = await client.post(
                    f"{self.config['api_base_url']}/ask",
                    json={"query": query}
                )
                
                if ask_response.status_code == 200:
                    result = ask_response.json()
                    
                    # Validate pipeline components
                    has_answer = bool(result.get('answer'))
                    has_rows = len(result.get('rows', [])) > 0
                    has_intent = bool(result.get('intent'))
                    has_entities = len(result.get('entities', [])) > 0
                    has_metadata = bool(result.get('metadata'))
                    
                    pipeline_steps.extend([
                        ("Answer Generation", has_answer),
                        ("Data Retrieval", has_rows),
                        ("Intent Recognition", has_intent),
                        ("Entity Grounding", has_entities),
                        ("Metadata Collection", has_metadata)
                    ])
                else:
                    pipeline_steps.append(("Full Pipeline", False))
                
                # Step 3: Subgraph generation
                subgraph_response = await client.get(
                    f"{self.config['api_base_url']}/graph/subgraph",
                    params={"ticker": "SPY", "top": 5}
                )
                pipeline_steps.append(("Subgraph Generation", subgraph_response.status_code == 200))
            
            successful_steps = sum(1 for _, success in pipeline_steps if success)
            total_steps = len(pipeline_steps)
            
            status = "PASS" if successful_steps >= total_steps * 0.8 else "FAIL"
            details = f"Pipeline integration: {successful_steps}/{total_steps} steps successful"
            
            self._add_result(TestResult(
                name="Full Pipeline Integration",
                category="Integration",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'successful_steps': successful_steps,
                    'total_steps': total_steps,
                    'step_details': dict(pipeline_steps)
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Full Pipeline Integration",
                category="Integration",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_data_flow(self):
        """Test data flow from database to UI."""
        start_time = time.time()
        
        try:
            flow_checks = []
            
            # Check 1: Database has data
            driver = AsyncGraphDatabase.driver(
                self.config['neo4j_uri'],
                auth=(self.config['neo4j_user'], self.config['neo4j_password'])
            )
            
            async with driver.session() as session:
                result = await session.run("MATCH (e:ETF)-[h:HOLDS]->(c:Company) RETURN count(h) as holdings_count")
                holdings_count = (await result.single())['holdings_count']
                flow_checks.append(("Database Data", holdings_count > 0))
            
            await driver.close()
            
            # Check 2: API serves data
            async with httpx.AsyncClient(timeout=self.config['test_timeout']) as client:
                response = await client.post(
                    f"{self.config['api_base_url']}/ask",
                    json={"query": "SPY holdings"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    api_has_data = len(result.get('rows', [])) > 0
                    flow_checks.append(("API Data Serving", api_has_data))
                else:
                    flow_checks.append(("API Data Serving", False))
                
                # Check 3: UI is accessible
                ui_response = await client.get(self.config['ui_base_url'])
                flow_checks.append(("UI Accessibility", ui_response.status_code == 200))
            
            successful_checks = sum(1 for _, success in flow_checks if success)
            total_checks = len(flow_checks)
            
            status = "PASS" if successful_checks == total_checks else "FAIL"
            details = f"Data flow validation: {successful_checks}/{total_checks} checks passed"
            
            self._add_result(TestResult(
                name="Data Flow Validation",
                category="Integration",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'successful_checks': successful_checks,
                    'total_checks': total_checks,
                    'holdings_count': holdings_count,
                    'flow_details': dict(flow_checks)
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Data Flow Validation",
                category="Integration",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    async def _test_load_performance(self):
        """Test system performance under load."""
        start_time = time.time()
        
        try:
            # Simulate concurrent requests
            concurrent_requests = 5
            request_times = []
            error_count = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create concurrent tasks
                async def make_request(query_id):
                    try:
                        request_start = time.time()
                        response = await client.post(
                            f"{self.config['api_base_url']}/ask",
                            json={"query": f"SPY holdings test {query_id}"}
                        )
                        request_time = (time.time() - request_start) * 1000
                        return request_time, response.status_code
                    except Exception:
                        return None, None
                
                # Execute concurrent requests
                tasks = [make_request(i) for i in range(concurrent_requests)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, tuple) and result[0] is not None:
                        request_time, status_code = result
                        request_times.append(request_time)
                        if status_code != 200:
                            error_count += 1
                    else:
                        error_count += 1
            
            if request_times:
                avg_response_time = sum(request_times) / len(request_times)
                max_response_time = max(request_times)
                success_rate = (len(request_times) - error_count) / concurrent_requests
            else:
                avg_response_time = float('inf')
                max_response_time = float('inf')
                success_rate = 0
            
            threshold = self.config['performance_thresholds']['api_response_time_ms'] * 2  # Allow 2x for concurrent
            
            status = "PASS" if success_rate >= 0.8 and avg_response_time < threshold else "WARN"
            details = f"Load test: {success_rate:.1%} success rate, {avg_response_time:.0f}ms avg response"
            
            self._add_result(TestResult(
                name="Load Performance",
                category="Integration",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                details=details,
                metrics={
                    'concurrent_requests': concurrent_requests,
                    'success_rate': success_rate,
                    'avg_response_time_ms': avg_response_time,
                    'max_response_time_ms': max_response_time,
                    'error_count': error_count
                }
            ))
            
        except Exception as e:
            self._add_result(TestResult(
                name="Load Performance",
                category="Integration",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            ))

    def _add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)
        status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}
        logger.info(f"{status_emoji.get(result.status, '❓')} {result.name}: {result.status} ({result.duration_ms:.0f}ms)")
        if result.error:
            logger.error(f"   Error: {result.error}")
        elif result.details:
            logger.info(f"   {result.details}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            'platform': platform.system(),
            'version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'timestamp': datetime.now().isoformat()
        }

    def _generate_report(self, system_info: Dict[str, Any]) -> TestReport:
        """Generate comprehensive test report."""
        total_duration = (time.time() - self.start_time) * 1000
        
        # Count results by status
        status_counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        # Generate summary
        summary = {
            'overall_status': 'PASS' if status_counts['FAIL'] == 0 else 'FAIL',
            'pass_rate': status_counts['PASS'] / len(self.results) if self.results else 0,
            'categories': {},
            'recommendations': []
        }
        
        # Category breakdown
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
            categories[result.category][result.status] += 1
        
        summary['categories'] = categories
        
        # Generate recommendations
        if status_counts['FAIL'] > 0:
            summary['recommendations'].append("Address failing tests before production deployment")
        if status_counts['WARN'] > 0:
            summary['recommendations'].append("Review warnings for potential performance or reliability issues")
        if status_counts['PASS'] / len(self.results) < 0.9 if self.results else True:
            summary['recommendations'].append("Improve test coverage and system reliability")
        
        return TestReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.results),
            passed=status_counts['PASS'],
            failed=status_counts['FAIL'],
            skipped=status_counts['SKIP'],
            warnings=status_counts['WARN'],
            total_duration_ms=total_duration,
            system_info=system_info,
            results=self.results,
            summary=summary
        )

    def _print_report(self, report: TestReport, format_type: str = "text"):
        """Print test report."""
        if format_type == "json":
            print(json.dumps(asdict(report), indent=2, default=str))
            return
        
        # Text format
        print("\n" + "="*80)
        print("🧪 ETF GRAPHRAG SYSTEM - COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY")
        print(f"   Total Tests: {report.total_tests}")
        print(f"   Passed: {report.passed} ✅")
        print(f"   Failed: {report.failed} ❌")
        print(f"   Warnings: {report.warnings} ⚠️")
        print(f"   Skipped: {report.skipped} ⏭️")
        print(f"   Pass Rate: {report.summary['pass_rate']:.1%}")
        print(f"   Total Duration: {report.total_duration_ms:.0f}ms")
        print(f"   Overall Status: {report.summary['overall_status']}")
        
        print(f"\n🏗️ SYSTEM INFO")
        print(f"   Platform: {report.system_info['platform']} {report.system_info['version']}")
        print(f"   Python: {report.system_info['python_version']}")
        print(f"   CPU: {report.system_info['cpu_count']} cores")
        print(f"   Memory: {report.system_info['memory_gb']:.1f}GB")
        
        print(f"\n📋 CATEGORY BREAKDOWN")
        for category, counts in report.summary['categories'].items():
            total = sum(counts.values())
            pass_rate = counts['PASS'] / total if total > 0 else 0
            print(f"   {category}: {counts['PASS']}/{total} passed ({pass_rate:.1%})")
        
        if report.failed > 0:
            print(f"\n❌ FAILED TESTS")
            for result in report.results:
                if result.status == "FAIL":
                    print(f"   • {result.name} ({result.category})")
                    if result.error:
                        print(f"     Error: {result.error}")
        
        if report.warnings > 0:
            print(f"\n⚠️ WARNINGS")
            for result in report.results:
                if result.status == "WARN":
                    print(f"   • {result.name} ({result.category})")
                    if result.details:
                        print(f"     Details: {result.details}")
        
        if report.summary['recommendations']:
            print(f"\n💡 RECOMMENDATIONS")
            for rec in report.summary['recommendations']:
                print(f"   • {rec}")
        
        print(f"\n📝 DETAILED RESULTS")
        current_category = None
        for result in sorted(report.results, key=lambda x: (x.category, x.name)):
            if result.category != current_category:
                current_category = result.category
                print(f"\n   {current_category}:")
            
            status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}
            print(f"     {status_emoji.get(result.status, '❓')} {result.name} ({result.duration_ms:.0f}ms)")
            
            if result.details:
                print(f"        {result.details}")
            if result.error:
                print(f"        Error: {result.error}")
        
        print("\n" + "="*80)
        
        # Save detailed report to file
        report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        print(f"📄 Detailed report saved to: {report_file}")


async def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="Comprehensive ETF GraphRAG System Tests")
    parser.add_argument("--no-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--report-format", choices=["text", "json"], default="text", help="Report format")
    
    args = parser.parse_args()
    
    # Create test suite
    test_suite = ComprehensiveTestSuite()
    
    try:
        # Run tests
        report = await test_suite.run_all_tests(skip_integration=args.no_integration)
        
        # Print report
        test_suite._print_report(report, args.report_format)
        
        # Exit with appropriate code
        exit_code = 0 if report.failed == 0 else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Test suite failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure required dependencies
    try:
        import httpx
        import neo4j
        import psutil
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Install with: pip install httpx neo4j psutil")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())