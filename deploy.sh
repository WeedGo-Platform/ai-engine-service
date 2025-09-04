#!/bin/bash

# WeedGo AI Engine Deployment Script
# This script deploys the complete AI engine with LLM, Knowledge Graph, and ML infrastructure

set -e

echo "🚀 WeedGo AI Engine Deployment Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_status "Docker installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_status "Docker Compose installed"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. Some scripts may not work."
    else
        print_status "Python 3 installed"
    fi
}

# Create necessary directories
setup_directories() {
    echo "Setting up directories..."
    
    mkdir -p models
    mkdir -p data/migrations
    mkdir -p data/ontology
    mkdir -p logs
    mkdir -p config
    
    print_status "Directories created"
}

# Download models
download_models() {
    echo "Downloading AI models..."
    
    # Create models directory
    cd models
    
    # Download Llama 2 7B model (GGUF format for llama-cpp)
    if [ ! -f "llama-2-7b-chat.Q4_K_M.gguf" ]; then
        print_warning "Downloading Llama 2 7B model (this may take a while)..."
        wget -q --show-progress https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
        print_status "Llama 2 model downloaded"
    else
        print_status "Llama 2 model already exists"
    fi
    
    # Download Mistral 7B model as backup
    if [ ! -f "mistral-7b-instruct-v0.2.Q4_K_M.gguf" ]; then
        print_warning "Downloading Mistral 7B model (backup model)..."
        wget -q --show-progress https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
        print_status "Mistral model downloaded"
    else
        print_status "Mistral model already exists"
    fi
    
    cd ..
}

# Install Python dependencies
install_python_deps() {
    echo "Installing Python dependencies..."
    
    if command -v python3 &> /dev/null; then
        pip3 install -q --upgrade pip
        pip3 install -q -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_warning "Skipping Python dependencies (Python not installed)"
    fi
}

# Start services
start_services() {
    echo "Starting Docker services..."
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
    
    # Start infrastructure services first
    print_status "Starting infrastructure services..."
    docker-compose up -d postgres redis etcd minio
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL..."
    sleep 10
    
    # Start vector databases
    print_status "Starting vector and graph databases..."
    docker-compose up -d milvus neo4j elasticsearch
    
    # Wait for databases to be ready
    echo "Waiting for databases to initialize..."
    sleep 20
    
    # Initialize databases
    initialize_databases
    
    # Start AI engine
    print_status "Starting AI engine service..."
    docker-compose up -d ai-engine
    
    # Start monitoring
    print_status "Starting monitoring services..."
    docker-compose up -d prometheus grafana mlflow
    
    print_status "All services started successfully!"
}

# Initialize databases
initialize_databases() {
    echo "Initializing databases..."
    
    # Initialize PostgreSQL schema
    print_status "Creating PostgreSQL schema..."
    PGPASSWORD=weedgo123 psql -h localhost -p 5434 -U weedgo -d ai_engine << EOF
-- Products table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(100),
    strain_type VARCHAR(50),
    thc_content DECIMAL(5,2),
    cbd_content DECIMAL(5,2),
    terpenes JSONB,
    effects TEXT[],
    description TEXT,
    price DECIMAL(10,2),
    inventory_count INTEGER DEFAULT 0,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    birth_date DATE,
    preferences JSONB,
    medical_conditions TEXT[],
    purchase_history JSONB,
    loyalty_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    customer_id VARCHAR(255),
    message TEXT,
    response TEXT,
    intent VARCHAR(100),
    entities JSONB,
    confidence DECIMAL(3,2),
    feedback INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(255),
    product_id UUID,
    recommendation_type VARCHAR(50),
    score DECIMAL(3,2),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    customer_id VARCHAR(255),
    product_id UUID,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_strain ON products(strain_type);
CREATE INDEX idx_chat_session ON chat_history(session_id);
CREATE INDEX idx_chat_customer ON chat_history(customer_id);
CREATE INDEX idx_recommendations_customer ON recommendations(customer_id);
CREATE INDEX idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_customer ON analytics_events(customer_id);

-- MLflow tables
CREATE SCHEMA IF NOT EXISTS mlflow;
EOF
    
    print_status "Database schema created"
}

# Load sample data
load_sample_data() {
    echo "Loading sample data..."
    
    if [ -f "scripts/load_complete_data.py" ]; then
        python3 scripts/load_complete_data.py
        print_status "Sample data loaded"
    else
        print_warning "Sample data script not found, skipping..."
    fi
}

# Build knowledge graph
build_knowledge_graph() {
    echo "Building knowledge graph..."
    
    if [ -f "scripts/build_knowledge_graph.py" ]; then
        python3 scripts/build_knowledge_graph.py
        print_status "Knowledge graph built"
    else
        print_warning "Knowledge graph script not found, skipping..."
    fi
}

# Health check
health_check() {
    echo "Performing health checks..."
    
    # Check AI Engine API
    if curl -s http://localhost:8000/health > /dev/null; then
        print_status "AI Engine API is healthy"
    else
        print_warning "AI Engine API is not responding"
    fi
    
    # Check Neo4j
    if curl -s http://localhost:7474 > /dev/null; then
        print_status "Neo4j is accessible"
    else
        print_warning "Neo4j is not responding"
    fi
    
    # Check Elasticsearch
    if curl -s http://localhost:9200/_cluster/health > /dev/null; then
        print_status "Elasticsearch is healthy"
    else
        print_warning "Elasticsearch is not responding"
    fi
    
    # Check Milvus
    if curl -s http://localhost:9091/healthz > /dev/null; then
        print_status "Milvus is healthy"
    else
        print_warning "Milvus is not responding"
    fi
}

# Print access information
print_access_info() {
    echo ""
    echo "========================================="
    echo "🎉 WeedGo AI Engine Deployment Complete!"
    echo "========================================="
    echo ""
    echo "Access Points:"
    echo "  • AI Engine API: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Neo4j Browser: http://localhost:7474 (user: neo4j, pass: weedgo123)"
    echo "  • Elasticsearch: http://localhost:9200"
    echo "  • MLflow: http://localhost:5000"
    echo "  • Grafana: http://localhost:3000 (user: admin, pass: admin)"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • MinIO Console: http://localhost:9001 (user: minioadmin, pass: minioadmin)"
    echo ""
    echo "Test the Virtual Budtender:"
    echo "  curl -X POST http://localhost:8000/api/v2/budtender/chat \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"message\": \"I need help with anxiety and sleep issues\", \"session_id\": \"test-session\"}'"
    echo ""
    echo "View logs:"
    echo "  docker-compose logs -f ai-engine"
    echo ""
    echo "Stop services:"
    echo "  docker-compose down"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "======================================"
    echo "WeedGo AI Engine Deployment Script"
    echo "======================================"
    echo ""
    
    check_prerequisites
    setup_directories
    download_models
    install_python_deps
    start_services
    
    # Wait for services to stabilize
    echo "Waiting for all services to stabilize..."
    sleep 10
    
    load_sample_data
    build_knowledge_graph
    health_check
    print_access_info
}

# Run main function
main