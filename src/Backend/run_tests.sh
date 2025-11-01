#!/bin/bash
# WeedGo Test Runner
# Comprehensive test execution script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}WeedGo Test Suite${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}>>> $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Parse command line arguments
TEST_TYPE=${1:-all}
COVERAGE=${2:-no}

# Setup test database
print_header "Setting up test database..."

# Create test database if it doesn't exist
PGPASSWORD=weedgo123 psql -h localhost -p 5434 -U weedgo -d postgres -c "CREATE DATABASE ai_engine_test;" 2>/dev/null || true

# Run migrations on test database
print_header "Running migrations on test database..."
for migration in migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "  Applying $(basename $migration)..."
        PGPASSWORD=weedgo123 psql -h localhost -p 5434 -U weedgo -d ai_engine_test -f "$migration" > /dev/null 2>&1 || true
    fi
done

print_success "Test database ready"

# Install test dependencies
print_header "Checking test dependencies..."
pip install -q -r requirements-test.txt
print_success "Dependencies installed"

# Run tests based on type
case $TEST_TYPE in
    "unit")
        print_header "Running UNIT tests..."
        pytest tests/unit/ -v -m unit
        ;;

    "integration")
        print_header "Running INTEGRATION tests..."
        pytest tests/integration/ -v -m integration
        ;;

    "concurrency")
        print_header "Running CONCURRENCY tests (CRITICAL)..."
        pytest tests/concurrency/ -v -m concurrency --tb=short
        ;;

    "e2e")
        print_header "Running END-TO-END tests..."
        pytest tests/e2e/ -v -m e2e
        ;;

    "smoke")
        print_header "Running SMOKE tests (quick sanity check)..."
        pytest tests/ -v -m smoke --maxfail=1
        ;;

    "security")
        print_header "Running SECURITY tests..."
        pytest tests/ -v -m security
        ;;

    "critical")
        print_header "Running CRITICAL tests (concurrency + security)..."
        pytest tests/ -v -m "concurrency or security"
        ;;

    "all")
        print_header "Running ALL tests..."

        if [ "$COVERAGE" = "coverage" ]; then
            pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
        else
            pytest tests/ -v
        fi
        ;;

    "fast")
        print_header "Running FAST tests (unit + smoke)..."
        pytest tests/ -v -m "unit or smoke" --maxfail=3
        ;;

    *)
        print_error "Unknown test type: $TEST_TYPE"
        echo ""
        echo "Usage: ./run_tests.sh [TYPE] [coverage]"
        echo ""
        echo "Test types:"
        echo "  unit         - Unit tests only"
        echo "  integration  - Integration tests only"
        echo "  concurrency  - Concurrency/race condition tests (CRITICAL)"
        echo "  e2e          - End-to-end tests"
        echo "  smoke        - Quick smoke tests"
        echo "  security     - Security tests"
        echo "  critical     - Critical tests (concurrency + security)"
        echo "  fast         - Fast tests (unit + smoke)"
        echo "  all          - All tests (default)"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh concurrency        # Run cart locking tests"
        echo "  ./run_tests.sh all coverage       # All tests with coverage"
        echo "  ./run_tests.sh fast                # Quick validation"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    print_success "All tests passed!"
    echo ""
    echo -e "${BLUE}=================================${NC}"
    echo -e "${GREEN}✅ TEST SUITE PASSED${NC}"
    echo -e "${BLUE}=================================${NC}"
else
    print_error "Some tests failed!"
    echo ""
    echo -e "${BLUE}=================================${NC}"
    echo -e "${RED}❌ TEST SUITE FAILED${NC}"
    echo -e "${BLUE}=================================${NC}"
    exit 1
fi
