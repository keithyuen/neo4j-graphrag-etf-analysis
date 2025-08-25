#!/bin/bash

# ETF GraphRAG System - Comprehensive Test Runner
# Usage: ./run_tests.sh [quick|full|json] [--no-integration]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    print_status "Python version: $(python3 --version)"
}

# Check and install test dependencies
install_deps() {
    print_status "Checking test dependencies..."
    
    if [ -f "$SCRIPT_DIR/test-requirements.txt" ]; then
        print_status "Installing test dependencies..."
        pip3 install -r "$SCRIPT_DIR/test-requirements.txt" --quiet
        print_success "Dependencies installed"
    else
        print_warning "test-requirements.txt not found, installing basic dependencies..."
        pip3 install httpx neo4j psutil --quiet
    fi
}

# Check if services are running
check_services() {
    print_status "Checking system services..."
    
    # Check Neo4j
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        print_success "Neo4j is running (port 7474)"
    else
        print_warning "Neo4j may not be running (port 7474 not accessible)"
    fi
    
    # Check API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API is running (port 8000)"
    else
        print_warning "API may not be running (port 8000 not accessible)"
    fi
    
    # Check UI
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "UI is running (port 3000)"
    else
        print_warning "UI may not be running (port 3000 not accessible)"
    fi
    
    # Check Ollama
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        print_success "Ollama is running (port 11434)"
    else
        print_warning "Ollama may not be running (port 11434 not accessible)"
    fi
}

# Run the comprehensive test suite
run_tests() {
    local test_mode="$1"
    local extra_args="$2"
    
    print_status "Running comprehensive test suite..."
    print_status "Mode: $test_mode"
    
    cd "$SCRIPT_DIR"
    
    case "$test_mode" in
        "quick")
            print_status "Running quick tests (no integration)..."
            python3 comprehensive_test.py --no-integration $extra_args
            ;;
        "json")
            print_status "Running full tests with JSON output..."
            python3 comprehensive_test.py --report-format json $extra_args
            ;;
        "full"|*)
            print_status "Running full test suite..."
            python3 comprehensive_test.py $extra_args
            ;;
    esac
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "All tests completed successfully!"
    else
        print_error "Some tests failed (exit code: $exit_code)"
    fi
    
    return $exit_code
}

# Show usage information
show_usage() {
    echo "ETF GraphRAG System - Comprehensive Test Runner"
    echo ""
    echo "Usage: $0 [MODE] [OPTIONS]"
    echo ""
    echo "Modes:"
    echo "  quick    Run tests without integration tests (faster)"
    echo "  full     Run all tests including integration tests (default)"
    echo "  json     Run all tests with JSON output format"
    echo ""
    echo "Options:"
    echo "  --no-integration    Skip integration tests"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run full test suite"
    echo "  $0 quick            # Run quick tests only"
    echo "  $0 json             # Full tests with JSON output"
    echo "  $0 full --no-integration  # Full tests but skip integration"
    echo ""
    echo "Prerequisites:"
    echo "  - Python 3.7+"
    echo "  - Neo4j running on port 7687"
    echo "  - API running on port 8000"
    echo "  - UI running on port 3000 (for UI tests)"
    echo "  - Ollama running on port 11434 (for LLM tests)"
    echo ""
    echo "To start all services:"
    echo "  docker-compose up -d"
}

# Parse command line arguments
MODE="full"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        "quick"|"full"|"json")
            MODE="$1"
            shift
            ;;
        --no-integration)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "🧪 ETF GraphRAG System - Comprehensive Test Runner"
    echo "=================================================="
    echo ""
    
    check_python
    install_deps
    check_services
    
    echo ""
    run_tests "$MODE" "$EXTRA_ARGS"
    
    local final_exit_code=$?
    
    echo ""
    if [ $final_exit_code -eq 0 ]; then
        print_success "🎉 Test execution completed successfully!"
        echo ""
        echo "Next steps:"
        echo "  - Review test report files for detailed results"
        echo "  - Check logs for any warnings or issues"
        echo "  - Deploy system if all tests pass"
    else
        print_error "❌ Test execution completed with failures"
        echo ""
        echo "Next steps:"
        echo "  - Review failed tests in the output above"
        echo "  - Check service logs for error details"
        echo "  - Fix issues and re-run tests"
    fi
    
    exit $final_exit_code
}

# Run main function
main "$@"