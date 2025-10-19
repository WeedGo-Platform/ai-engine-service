#!/bin/bash

##############################################################################
# Multilingual Translation Testing Script
# Runs comprehensive UI tests across all 28 languages
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Header
echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════"
echo "       MULTILINGUAL TRANSLATION TESTING SUITE"
echo "       Testing 28 Languages × 21 Namespaces"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Create test results directory
mkdir -p test-results/screenshots

# Test mode
TEST_MODE="${1:-all}"

log_info "Test Mode: $TEST_MODE"
echo ""

# Function to run a test suite
run_test_suite() {
    local suite_name=$1
    local suite_script=$2

    log_info "Running: $suite_name"

    if npm run "$suite_script"; then
        log_success "$suite_name - PASSED"
        return 0
    else
        log_error "$suite_name - FAILED"
        return 1
    fi
}

# Test execution based on mode
case $TEST_MODE in
    "all")
        log_info "Running ALL test suites..."
        echo ""

        run_test_suite "Language Switching Tests" "test:language"
        echo ""

        run_test_suite "RTL Layout Tests" "test:rtl"
        echo ""

        run_test_suite "Translation Sanity Tests" "test:sanity"
        echo ""

        run_test_suite "Performance Tests" "test:performance"
        echo ""

        run_test_suite "Comprehensive UI Tests" "test:comprehensive"
        ;;

    "quick")
        log_info "Running QUICK test suite..."
        echo ""

        run_test_suite "Language Switching Tests" "test:language"
        echo ""

        run_test_suite "RTL Layout Tests" "test:rtl"
        ;;

    "rtl")
        log_info "Running RTL-specific tests..."
        echo ""

        run_test_suite "RTL Layout Tests" "test:rtl"
        ;;

    "sanity")
        log_info "Running Translation Sanity tests..."
        echo ""

        run_test_suite "Translation Sanity Tests" "test:sanity"
        ;;

    "performance")
        log_info "Running Performance tests..."
        echo ""

        run_test_suite "Performance Tests" "test:performance"
        ;;

    *)
        log_error "Unknown test mode: $TEST_MODE"
        echo ""
        echo "Usage: ./run-translation-tests.sh [mode]"
        echo ""
        echo "Available modes:"
        echo "  all          - Run all test suites (default)"
        echo "  quick        - Run quick tests (language switching + RTL)"
        echo "  rtl          - Run RTL layout tests only"
        echo "  sanity       - Run translation sanity tests only"
        echo "  performance  - Run performance tests only"
        exit 1
        ;;
esac

# Generate summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                     TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Show test results location
log_info "Test Results:"
echo "  📊 HTML Report: playwright-report/index.html"
echo "  📋 JSON Report: test-results/results.json"
echo "  📸 Screenshots: test-results/screenshots/"
echo ""

# Open report (macOS)
if [ "$(uname)" == "Darwin" ]; then
    log_info "Opening test report..."
    npm run test:report
fi

log_success "Translation testing complete!"
echo ""
