# ETF GraphRAG System - Testing Guide

This directory contains comprehensive testing tools for the ETF GraphRAG system.

## 🧪 Test Scripts

### 1. `comprehensive_test.py`
**Main comprehensive testing script** that validates all system components systematically.

**Features:**
- **Database Layer Tests**: Neo4j connectivity, schema validation, data integrity, relationships, query performance
- **API Layer Tests**: All endpoints, GraphRAG pipeline, security, error handling, performance
- **UI Layer Tests**: Accessibility, API integration, basic functionality  
- **Integration Tests**: Full pipeline validation, data flow, load testing

**Usage:**
```bash
# Run all tests
python3 comprehensive_test.py

# Skip integration tests (faster)
python3 comprehensive_test.py --no-integration

# JSON output format
python3 comprehensive_test.py --report-format json
```

**Output:**
- Detailed console output with test progress
- Test report saved to timestamped JSON file
- Log file with detailed execution information

### 2. `run_tests.sh`
**Convenient wrapper script** for running the comprehensive test suite.

**Features:**
- Service health checks before testing
- Automatic dependency installation
- Multiple test modes
- Colored output and progress indicators

**Usage:**
```bash
# Quick tests (no integration)
./run_tests.sh quick

# Full test suite (default)
./run_tests.sh full

# Full tests with JSON output
./run_tests.sh json

# Show help
./run_tests.sh --help
```

### 3. `run_all_tests.sh`
**Complete test suite runner** that executes ALL available tests in the project.

**Test Categories:**
1. Service Health Check
2. Code Quality Checks (linting)
3. API Unit Tests (pytest)
4. UI Unit Tests (vitest)
5. Comprehensive System Tests

**Usage:**
```bash
# Run all test categories
./run_all_tests.sh

# Skip integration tests
./run_all_tests.sh --no-integration

# Skip unit tests, only run system tests
./run_all_tests.sh --skip-unit

# Skip code quality checks
./run_all_tests.sh --skip-quality
```

## 📋 Prerequisites

### System Requirements
- **Python 3.7+** with pip
- **Node.js** with npm (for UI tests)
- **Docker** and Docker Compose
- **Internet connection** (for dependency installation)

### Running Services
Before running tests, ensure all services are running:

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View service logs
docker-compose logs -f
```

### Service Endpoints
- **Neo4j Browser**: http://localhost:7474
- **Neo4j Bolt**: bolt://localhost:7687
- **API**: http://localhost:8000
- **UI**: http://localhost:3000
- **Ollama**: http://localhost:11434

## 📊 Test Categories Explained

### Database Layer Tests
- **Neo4j Connectivity**: Basic connection and authentication
- **Schema Validation**: Verifies node labels, relationships, constraints
- **Data Integrity**: Checks for missing data, orphaned nodes, invalid weights
- **Relationship Validation**: Validates HOLDS and IN_SECTOR relationships
- **Query Performance**: Benchmarks common query patterns

### API Layer Tests
- **Health Check**: Verifies API is accessible and responding
- **Security**: Tests for SQL injection, XSS, payload limits
- **Ask Endpoint**: Tests GraphRAG query processing end-to-end
- **Intent Endpoint**: Validates intent classification functionality
- **Graph Endpoint**: Tests subgraph generation
- **ETL Endpoints**: Tests data refresh and cache management
- **Error Handling**: Validates proper error responses
- **Performance**: Measures API response times under load

### UI Layer Tests
- **Accessibility**: Basic HTML structure and accessibility features
- **API Integration**: Tests if UI can communicate with API
- **Functionality**: Validates core UI components and routing

### Integration Tests
- **Full Pipeline**: Tests complete GraphRAG workflow
- **Data Flow**: Validates data flow from database through API to UI
- **Load Performance**: Tests system behavior under concurrent load

## 🎯 Performance Thresholds

The tests include performance thresholds that can be configured:

- **API Response Time**: 2000ms (2 seconds)
- **Database Query Time**: 1000ms (1 second)
- **UI Load Time**: 5000ms (5 seconds)

Tests will show warnings if these thresholds are exceeded.

## 📈 Test Reports

### Console Output
- Real-time test progress with colored status indicators
- Summary statistics and pass/fail rates
- Category-wise breakdown
- Recommendations for failures

### File Output
- **JSON Report**: Detailed machine-readable test results
- **Log File**: Complete execution log with timestamps
- **Summary File**: High-level test results summary

### Example Report Structure
```json
{
  "timestamp": "2025-08-18T10:30:00",
  "total_tests": 25,
  "passed": 22,
  "failed": 2,
  "warnings": 1,
  "total_duration_ms": 45000,
  "system_info": {...},
  "results": [...],
  "summary": {...}
}
```

## 🚨 Troubleshooting

### Common Issues

**Services Not Running**
```bash
# Check if services are up
docker-compose ps

# Start services
docker-compose up -d

# Check logs for errors
docker-compose logs api
```

**Python Dependencies Missing**
```bash
# Install test dependencies
pip3 install -r test-requirements.txt

# Or manually install
pip3 install httpx neo4j psutil
```

**Permission Errors**
```bash
# Make scripts executable
chmod +x *.sh
```

**Neo4j Connection Issues**
- Verify Neo4j is running: `docker-compose ps`
- Check credentials in config
- Ensure port 7687 is not blocked

**API Connection Issues**  
- Verify API health: `curl http://localhost:8000/health`
- Check API logs: `docker-compose logs api`
- Ensure port 8000 is not blocked

### Test Failures

**Database Tests Failing**
- Check if data has been loaded: Review ETL logs
- Verify schema setup: Check Neo4j browser
- Check constraints: Run `SHOW CONSTRAINTS` in Neo4j

**API Tests Failing**
- Check if Ollama is running and has the required model
- Verify API configuration
- Check for recent code changes affecting endpoints

**Integration Tests Failing**
- Usually indicates system-wide issues
- Check all service logs
- Verify end-to-end data flow manually

## 🛠️ Customizing Tests

### Adding New Tests
1. Add test methods to `ComprehensiveTestSuite` class
2. Call new tests from appropriate `_run_*_tests()` methods
3. Use `_add_result()` to record test outcomes

### Modifying Thresholds
Edit the `performance_thresholds` in the `config` dictionary:

```python
'performance_thresholds': {
    'api_response_time_ms': 3000,  # Increase to 3 seconds
    'database_query_time_ms': 500,  # Decrease to 500ms
    'ui_load_time_ms': 10000       # Increase to 10 seconds
}
```

### Custom Test Queries
Modify the `test_queries` list to include domain-specific queries:

```python
self.test_queries = [
    "Your custom test query here",
    "Another test query",
    # ... existing queries
]
```

## 📚 Related Documentation

- **Project README**: `../README.md`
- **API Documentation**: `../api/README.md`
- **UI Documentation**: `../ui/README.md`
- **Docker Setup**: `../docker-compose.yml`

## 🤝 Contributing

When adding new features:
1. Write corresponding tests
2. Update test documentation
3. Ensure all tests pass before committing
4. Add performance benchmarks for critical paths

---

**Happy Testing!** 🎉