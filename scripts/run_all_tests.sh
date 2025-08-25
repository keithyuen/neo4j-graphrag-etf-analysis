#!/bin/bash

# ETF GraphRAG System - Complete Test Suite Runner
# This script runs ALL tests: unit tests, integration tests, and comprehensive system tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_section() {
    echo -e "${PURPLE}[SECTION]${NC} $1"
}

# Track test results
declare -a TEST_RESULTS

# Function to record test result
record_result() {
    local test_name="$1"
    local exit_code="$2"
    
    if [ $exit_code -eq 0 ]; then
        TEST_RESULTS+=("✅ $test_name")
        print_success "$test_name completed successfully"
    else
        TEST_RESULTS+=("❌ $test_name (exit code: $exit_code)")
        print_error "$test_name failed with exit code $exit_code"
    fi
}

# Function to run API unit tests
run_api_tests() {
    print_section "Running API Unit Tests"
    cd "$PROJECT_ROOT/api"
    
    if [ -f "requirements-test.txt" ]; then
        print_status "Installing API test dependencies..."
        pip3 install -r requirements-test.txt --quiet || {
            print_warning "Failed to install test dependencies, continuing..."
        }
    fi
    
    if [ -f "pytest.ini" ] && [ -d "tests" ]; then
        print_status "Running pytest for API..."
        python3 -m pytest tests/ -v --tb=short || {
            local exit_code=$?
            record_result "API Unit Tests" $exit_code
            return $exit_code
        }
        record_result "API Unit Tests" 0
    else
        print_warning "API tests not found or pytest not configured"
        record_result "API Unit Tests" 1
    fi
}

# Function to run UI unit tests
run_ui_tests() {
    print_section "Running UI Unit Tests"
    cd "$PROJECT_ROOT/ui"
    
    if [ -f "package.json" ]; then
        print_status "Checking npm dependencies..."
        if command -v npm &> /dev/null; then
            npm install --silent || {
                print_warning "Failed to install npm dependencies"
                record_result "UI Unit Tests" 1
                return 1
            }
            
            if npm run test --silent; then
                record_result "UI Unit Tests" 0
            else
                record_result "UI Unit Tests" 1
            fi
        else
            print_warning "npm not found, skipping UI tests"
            record_result "UI Unit Tests" 1
        fi
    else
        print_warning "UI package.json not found"
        record_result "UI Unit Tests" 1
    fi
}

# Function to run comprehensive system tests
run_comprehensive_tests() {
    print_section "Running Comprehensive System Tests"
    cd "$SCRIPT_DIR"
    
    if [ -f "comprehensive_test.py" ]; then
        # Install dependencies
        if [ -f "test-requirements.txt" ]; then
            print_status "Installing comprehensive test dependencies..."
            pip3 install -r test-requirements.txt --quiet || {
                print_warning "Failed to install test dependencies"
            }
        fi
        
        print_status "Running comprehensive system tests..."
        if python3 comprehensive_test.py "$@"; then
            record_result "Comprehensive System Tests" 0
        else
            local exit_code=$?
            record_result "Comprehensive System Tests" $exit_code
        fi
    else
        print_error "comprehensive_test.py not found"
        record_result "Comprehensive System Tests" 1
    fi
}

# Function to run linting and code quality checks
run_code_quality() {
    print_section "Running Code Quality Checks"
    
    # Python linting
    cd "$PROJECT_ROOT/api"
    if command -v flake8 &> /dev/null; then
        print_status "Running flake8 for Python code..."
        if flake8 app/ --max-line-length=100 --ignore=E203,W503; then
            record_result "Python Linting (flake8)" 0
        else
            record_result "Python Linting (flake8)" 1
        fi
    else
        print_warning "flake8 not found, skipping Python linting"
        record_result "Python Linting (flake8)" 1
    fi
    
    # JavaScript linting
    cd "$PROJECT_ROOT/ui"
    if [ -f "package.json" ] && command -v npm &> /dev/null; then
        if npm run lint --silent 2>/dev/null; then
            record_result "JavaScript Linting (ESLint)" 0
        else
            print_warning "ESLint not configured or failed"
            record_result "JavaScript Linting (ESLint)" 1
        fi
    else
        print_warning "npm or package.json not found, skipping JS linting"
        record_result "JavaScript Linting (ESLint)" 1
    fi
}

# Function to check service health
check_services() {
    print_section "Checking Service Health"
    
    local services_healthy=true
    
    # Check Neo4j
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        print_success "Neo4j is running (port 7474)"
    else
        print_warning "Neo4j not accessible on port 7474"
        services_healthy=false
    fi
    
    # Check API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API is running (port 8000)"
    else
        print_warning "API not accessible on port 8000"
        services_healthy=false
    fi
    
    # Check UI
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "UI is running (port 3000)"
    else
        print_warning "UI not accessible on port 3000"
        services_healthy=false
    fi
    
    # Check Ollama
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        print_success "Ollama is running (port 11434)"
    else
        print_warning "Ollama not accessible on port 11434"
        services_healthy=false
    fi
    
    if $services_healthy; then
        record_result "Service Health Check" 0
    else
        record_result "Service Health Check" 1
    fi
}

# Function to generate final report
generate_report() {
    print_section "Test Execution Summary"
    echo ""
    
    local total_tests=${#TEST_RESULTS[@]}
    local passed_tests=0
    local failed_tests=0
    
    for result in "${TEST_RESULTS[@]}"; do
        echo "  $result"
        if [[ $result == ✅* ]]; then
            ((passed_tests++))
        else
            ((failed_tests++))
        fi
    done
    
    echo ""
    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $failed_tests"
    
    if [ $failed_tests -eq 0 ]; then
        print_success "🎉 All test categories completed successfully!"
        echo ""
        echo "System is ready for deployment!"
        return 0
    else
        print_error "❌ Some test categories failed"
        echo ""
        echo "Please address the failing tests before deployment."
        return 1
    fi
}

# Show usage information
show_usage() {
    echo "ETF GraphRAG System - Complete Test Suite Runner"
    echo ""
    echo "This script runs ALL tests in the following order:"
    echo "  1. Service Health Check"
    echo "  2. Code Quality Checks (linting)"
    echo "  3. API Unit Tests (pytest)"
    echo "  4. UI Unit Tests (vitest)"
    echo "  5. Comprehensive System Tests"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-integration     Skip integration tests in comprehensive suite"
    echo "  --skip-unit         Skip unit tests (API and UI)"
    echo "  --skip-quality      Skip code quality checks"
    echo "  --skip-services     Skip service health checks"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all tests"
    echo "  $0 --no-integration          # Skip integration tests"
    echo "  $0 --skip-unit               # Only run system tests"
    echo "  $0 --skip-quality            # Skip linting"
    echo ""
    echo "Prerequisites:"
    echo "  - All services running (docker-compose up -d)"
    echo "  - Python 3.7+ with pip"
    echo "  - Node.js with npm (for UI tests)"
    echo "  - Internet connection (for dependency installation)"
}

# Parse command line arguments
SKIP_UNIT=false
SKIP_QUALITY=false
SKIP_SERVICES=false
COMPREHENSIVE_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-integration)
            COMPREHENSIVE_ARGS="$COMPREHENSIVE_ARGS $1"
            shift
            ;;
        --skip-unit)
            SKIP_UNIT=true
            shift
            ;;
        --skip-quality)
            SKIP_QUALITY=true
            shift
            ;;
        --skip-services)
            SKIP_SERVICES=true
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
    echo "🔬 ETF GraphRAG System - Complete Test Suite Runner"
    echo "======================================================"
    echo ""
    
    print_status "Python version: $(python3 --version)"
    if command -v node &> /dev/null; then
        print_status "Node.js version: $(node --version)"
    fi
    if command -v npm &> /dev/null; then
        print_status "npm version: $(npm --version)"
    fi
    
    echo ""
    
    # Run test categories
    if [ "$SKIP_SERVICES" = false ]; then
        check_services
        echo ""
    fi
    
    if [ "$SKIP_QUALITY" = false ]; then
        run_code_quality
        echo ""
    fi
    
    if [ "$SKIP_UNIT" = false ]; then
        run_api_tests
        echo ""
        run_ui_tests
        echo ""
    fi
    
    run_comprehensive_tests $COMPREHENSIVE_ARGS
    echo ""
    
    # Generate final report
    generate_report
    exit_code=$?
    
    # Save summary to file
    timestamp=$(date +"%Y%m%d_%H%M%S")
    summary_file="test_summary_$timestamp.txt"
    {
        echo "ETF GraphRAG System - Test Summary"
        echo "Generated: $(date)"
        echo ""
        for result in "${TEST_RESULTS[@]}"; do
            echo "$result"
        done
    } > "$summary_file"
    
    print_status "Test summary saved to: $summary_file"
    
    exit $exit_code
}

# Run main function
main "$@"