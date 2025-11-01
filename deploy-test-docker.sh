#!/bin/bash
#
# Deploy Test Environment to Local Docker
# This script automates the deployment of WeedGo test backend to local Docker
# Uses docker-compose.test.yml with .env.test configuration
#
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=6024
FRONTEND_PORT=6003
DB_PORT=5434
REDIS_PORT=6380
BACKEND_DIR="src/Backend"

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   WeedGo Test Backend - Docker Deployment        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check if Docker is installed
echo -e "${YELLOW}[1/7]${NC} Checking for Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found: $(docker --version)${NC}"
echo ""

# Step 2: Check if Docker Compose is installed
echo -e "${YELLOW}[2/7]${NC} Checking for Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    echo "Please install Docker Compose"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"
echo ""

# Step 3: Check if Docker daemon is running
echo -e "${YELLOW}[3/7]${NC} Checking Docker daemon..."
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon not running${NC}"
    echo "Please start Docker Desktop or Docker daemon"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon running${NC}"
echo ""

# Step 4: Navigate to backend directory and check .env.test
echo -e "${YELLOW}[4/7]${NC} Validating environment configuration..."
cd $BACKEND_DIR

if [ ! -f ".env.test" ]; then
    echo -e "${RED}✗ .env.test file not found${NC}"
    echo "Please ensure .env.test exists in $BACKEND_DIR"
    exit 1
fi
echo -e "${GREEN}✓ .env.test found${NC}"

# Run environment validation
echo "Running environment validation..."
if command -v python3 &> /dev/null && python3 -c "import dotenv" 2>/dev/null; then
    # Copy .env.test to .env for validation
    cp .env.test .env.validation.tmp
    if python3 validate_env.py > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Environment validation passed${NC}"
    else
        echo -e "${YELLOW}⚠ Environment validation warnings (non-blocking)${NC}"
    fi
    rm -f .env.validation.tmp
else
    echo -e "${YELLOW}⚠ python-dotenv not available, skipping validation${NC}"
fi
echo ""

# Step 5: Stop existing test containers (if any)
echo -e "${YELLOW}[5/7]${NC} Cleaning up existing test containers..."
if docker-compose -f docker-compose.test.yml ps -q 2>/dev/null | grep -q .; then
    echo "Stopping existing containers..."
    docker-compose -f docker-compose.test.yml down
    echo -e "${GREEN}✓ Existing containers stopped${NC}"
else
    echo -e "${GREEN}✓ No existing containers to clean up${NC}"
fi
echo ""

# Step 6: Build and start containers
echo -e "${YELLOW}[6/7]${NC} Building and starting Docker containers..."
echo "This may take 5-10 minutes for first build..."
echo ""

# Build images
echo "Building images..."
docker-compose -f docker-compose.test.yml build --no-cache

echo ""
echo "Starting containers..."
docker-compose -f docker-compose.test.yml up -d

echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Step 7: Wait for services to be healthy
echo -e "${YELLOW}[7/7]${NC} Waiting for services to be healthy..."
echo "This may take 30-60 seconds..."

MAX_WAIT=120
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check if backend is healthy
    if curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy!${NC}"
        break
    fi

    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Backend health check timed out${NC}"
    echo "Containers may still be starting. Check logs with:"
    echo -e "  ${BLUE}docker-compose -f docker-compose.test.yml logs -f${NC}"
else
    echo -e "${GREEN}✓ All services are healthy!${NC}"
fi
echo ""

# Show container status
echo -e "${BLUE}Container Status:${NC}"
docker-compose -f docker-compose.test.yml ps
echo ""

# Display deployment summary
echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Deployment Successful!                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service Endpoints:${NC}"
echo -e "  Backend:   ${BLUE}http://localhost:$BACKEND_PORT${NC}"
echo -e "  Health:    ${BLUE}http://localhost:$BACKEND_PORT/health${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  Database:  ${BLUE}localhost:$DB_PORT${NC}"
echo -e "  Redis:     ${BLUE}localhost:$REDIS_PORT${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test health endpoint:"
echo -e "   ${BLUE}curl http://localhost:$BACKEND_PORT/health${NC}"
echo ""
echo "2. View logs:"
echo -e "   ${BLUE}docker-compose -f docker-compose.test.yml logs -f ai-engine-test${NC}"
echo ""
echo "3. Start frontend on port $FRONTEND_PORT:"
echo -e "   ${BLUE}cd ../Frontend/ai-admin-dashboard && npm run dev${NC}"
echo ""
echo "4. Stop containers:"
echo -e "   ${BLUE}docker-compose -f docker-compose.test.yml down${NC}"
echo ""
echo -e "${GREEN}✓ Test environment ready!${NC}"
