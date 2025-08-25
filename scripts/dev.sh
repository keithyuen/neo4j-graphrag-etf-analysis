#!/bin/bash
set -e

# ETF GraphRAG Development Environment Setup
# This script sets up the complete development environment with one command

echo "🚀 Starting ETF GraphRAG development environment..."

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

# Check if Docker is running
print_status "Checking Docker availability..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi
print_success "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

# Check available memory (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    TOTAL_MEM=$(free -g | awk 'NR==2{printf "%.0f", $2}')
elif [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{printf "%.0f", $1/1024/1024/1024}')
else
    TOTAL_MEM=8  # Assume 8GB if we can't detect
fi

if [ "$TOTAL_MEM" -lt 8 ]; then
    print_warning "Your system has ${TOTAL_MEM}GB RAM. 8GB+ recommended for optimal performance."
else
    print_success "System memory: ${TOTAL_MEM}GB"
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_success "Created .env file from .env.example"
    print_warning "Please review and customize .env file for your environment"
else
    print_status ".env file already exists"
fi

# Determine Ollama profile (CPU vs GPU)
OLLAMA_PROFILE="cpu"
if command -v nvidia-smi >/dev/null 2>&1; then
    if nvidia-smi >/dev/null 2>&1; then
        print_status "NVIDIA GPU detected, using GPU profile for Ollama"
        OLLAMA_PROFILE="gpu"
    fi
else
    print_status "No GPU detected, using CPU profile for Ollama"
fi

# Set the profile in docker-compose
export COMPOSE_PROFILES="$OLLAMA_PROFILE"

print_status "Using Docker Compose profile: $OLLAMA_PROFILE"

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down >/dev/null 2>&1 || true

# Start core services first
print_status "Starting core services (Neo4j and Ollama)..."
docker-compose up -d neo4j ollama-$OLLAMA_PROFILE

# Wait for Neo4j to be ready
print_status "Waiting for Neo4j to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p password123 "RETURN 1" >/dev/null 2>&1; then
        print_success "Neo4j is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Neo4j failed to start after $max_attempts attempts"
        docker-compose logs neo4j
        exit 1
    fi
    
    echo -n "."
    sleep 2
    ((attempt++))
done

# Wait for Ollama to be ready
print_status "Waiting for Ollama to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T ollama-$OLLAMA_PROFILE curl -f http://localhost:11434/api/version >/dev/null 2>&1; then
        print_success "Ollama is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Ollama failed to start after $max_attempts attempts - continuing anyway"
        break
    fi
    
    echo -n "."
    sleep 2
    ((attempt++))
done

# Download Ollama models
print_status "Downloading Ollama models..."
OLLAMA_MODEL=$(grep OLLAMA_MODEL .env | cut -d '=' -f2 | tr -d '"' || echo "mistral:instruct")

if docker-compose exec -T ollama-$OLLAMA_PROFILE ollama list | grep -q "$OLLAMA_MODEL"; then
    print_success "Model $OLLAMA_MODEL already downloaded"
else
    print_status "Downloading model: $OLLAMA_MODEL (this may take several minutes)..."
    if docker-compose exec -T ollama-$OLLAMA_PROFILE ollama pull "$OLLAMA_MODEL"; then
        print_success "Model $OLLAMA_MODEL downloaded successfully"
    else
        print_warning "Failed to download model $OLLAMA_MODEL - LLM features may not work"
    fi
fi

# Initialize system (run schema setup and seed data)
print_status "Initializing system (schema and seed data)..."
if docker-compose run --rm init; then
    print_success "System initialization completed"
else
    print_error "System initialization failed"
    exit 1
fi

# Start application services
print_status "Starting application services (API and UI)..."
docker-compose up -d api ui

# Wait for API to be ready
print_status "Waiting for API to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "API is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "API failed to start after $max_attempts attempts"
        docker-compose logs api
        exit 1
    fi
    
    echo -n "."
    sleep 2
    ((attempt++))
done

# Wait for UI to be ready
print_status "Waiting for UI to be ready..."
max_attempts=20
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:3000/health >/dev/null 2>&1; then
        print_success "UI is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "UI failed to start after $max_attempts attempts"
        docker-compose logs ui
        exit 1
    fi
    
    echo -n "."
    sleep 2
    ((attempt++))
done

# Show final status
print_success "🎉 ETF GraphRAG development environment is ready!"
echo ""
echo "📊 Available Services:"
echo "  • Neo4j Browser:    http://localhost:7474 (neo4j/password123)"
echo "  • API:              http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • UI:               http://localhost:3000"
echo "  • Ollama:           http://localhost:11434"
echo ""
echo "🔧 Useful Commands:"
echo "  • View logs:        docker-compose logs -f [service]"
echo "  • Stop services:    docker-compose down"
echo "  • Restart service:  docker-compose restart [service]"
echo "  • Shell access:     docker-compose exec [service] bash"
echo ""
echo "📝 Test the system:"
echo "  • Open http://localhost:3000 in your browser"
echo "  • Try example query: 'What is SPY's exposure to AAPL?'"
echo "  • Check graph visualization at http://localhost:3000/graph"
echo ""

# Optional: Open browser automatically
if command -v open >/dev/null 2>&1; then
    # macOS
    print_status "Opening browser..."
    open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    print_status "Opening browser..."
    xdg-open http://localhost:3000
fi

print_success "Development environment setup completed! 🚀"