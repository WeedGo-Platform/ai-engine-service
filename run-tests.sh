#!/bin/bash

# WeedGo AI Engine Test Runner
# This script ensures the API is running and executes all tests

set -e

echo "🧪 WeedGo AI Engine Test Suite"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API is running
check_api() {
    echo -n "Checking if API is running at http://localhost:8080... "
    if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is running${NC}"
        return 0
    else
        echo -e "${RED}✗ API is not running${NC}"
        return 1
    fi
}

# Start API if not running
start_api() {
    echo -e "${YELLOW}Starting AI Engine API...${NC}"
    cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service
    python3 api_server.py > api_test.log 2>&1 &
    API_PID=$!
    echo "API started with PID: $API_PID"
    
    # Wait for API to be ready
    echo -n "Waiting for API to be ready"
    for i in {1..30}; do
        if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e " ${RED}✗ API failed to start${NC}"
    cat api_test.log
    exit 1
}

# Main execution
API_WAS_STARTED=false

if ! check_api; then
    start_api
    API_WAS_STARTED=true
fi

# Run tests
echo ""
echo "Running tests..."
echo "----------------"

cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/AIEngineTests

# Build the project first
echo "Building test project..."
dotnet build --configuration Release --nologo -v quiet

# Run tests with detailed output
echo ""
echo "Executing tests..."
dotnet test --configuration Release --no-build --logger "console;verbosity=normal" --logger "trx;LogFileName=test_results.trx"

TEST_EXIT_CODE=$?

# Generate test report
echo ""
echo "Test Summary:"
echo "-------------"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed. Check the output above for details.${NC}"
fi

# Cleanup
if [ "$API_WAS_STARTED" = true ]; then
    echo ""
    echo "Stopping API (PID: $API_PID)..."
    kill $API_PID 2>/dev/null || true
fi

echo ""
echo "Test run complete!"
exit $TEST_EXIT_CODE