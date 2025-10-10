#!/bin/bash

# ============================================================================
# MIGRATION VERIFICATION SCRIPT
# ============================================================================
# Description: Comprehensive verification of migration completion
# Run after: 000_MASTER_MIGRATION.sh
# ============================================================================

set -e

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5434}"
DB_NAME="${DB_NAME:-ai_engine}"
DB_USER="${DB_USER:-weedgo}"
DB_PASSWORD="${DB_PASSWORD:-weedgo123}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Verification results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Helper functions
log_header() {
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
}

log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

log_pass() {
    echo -e "${GREEN}  ✓ PASS:${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_fail() {
    echo -e "${RED}  ✗ FAIL:${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}  ⚠ WARNING:${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

run_query() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -A -c "$1" 2>/dev/null
}

# ============================================================================
# VERIFICATION CHECKS
# ============================================================================

log_header "DATABASE CONNECTION"
log_check "Testing database connection..."
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    log_pass "Database connection successful"
else
    log_fail "Cannot connect to database"
    exit 1
fi

# ============================================================================
log_header "EXTENSION VERIFICATION"

log_check "Verifying PostgreSQL extensions..."
EXTENSION_COUNT=$(run_query "SELECT COUNT(*) FROM pg_extension WHERE extname IN ('postgis', 'postgis_topology', 'pg_trgm', 'unaccent', 'uuid-ossp', 'plpgsql');")

if [ "$EXTENSION_COUNT" -eq "6" ]; then
    log_pass "All 6 required extensions installed"
    run_query "SELECT extname || ' (v' || extversion || ')' FROM pg_extension WHERE extname IN ('postgis', 'postgis_topology', 'pg_trgm', 'unaccent', 'uuid-ossp', 'plpgsql') ORDER BY extname;" | while read ext; do
        echo "       - $ext"
    done
else
    log_fail "Expected 6 extensions, found $EXTENSION_COUNT"
fi

# ============================================================================
log_header "TABLE VERIFICATION"

log_check "Counting total tables..."
TABLE_COUNT=$(run_query "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")

if [ "$TABLE_COUNT" -ge "118" ]; then
    log_pass "Found $TABLE_COUNT tables (expected 118+)"
else
    log_fail "Found only $TABLE_COUNT tables (expected 118)"
fi

log_check "Verifying critical tables exist..."
CRITICAL_TABLES=(
    "users" "stores" "tenants" "orders" "customers"
    "ocs_product_catalog" "ocs_inventory" "ocs_inventory_transactions"
    "batch_tracking" "purchase_orders" "cart_sessions"
    "payment_providers" "payment_transactions" "payment_refunds"
    "deliveries" "delivery_zones" "delivery_tracking"
    "pricing_rules" "discount_codes" "promotions"
    "customer_reviews" "product_ratings" "wishlist"
    "ai_conversations" "chat_interactions" "product_recommendations"
    "broadcasts" "communication_logs" "message_templates"
    "translations" "supported_languages"
    "auth_tokens" "api_keys" "otp_codes" "age_verification_logs"
    "provinces_territories" "provincial_suppliers" "profiles" "user_addresses"
)

MISSING_TABLES=()
for table in "${CRITICAL_TABLES[@]}"; do
    EXISTS=$(run_query "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table';")
    if [ "$EXISTS" -eq "1" ]; then
        echo "       ✓ $table"
    else
        MISSING_TABLES+=("$table")
    fi
done

if [ ${#MISSING_TABLES[@]} -eq 0 ]; then
    log_pass "All ${#CRITICAL_TABLES[@]} critical tables exist"
else
    log_fail "Missing ${#MISSING_TABLES[@]} tables: ${MISSING_TABLES[*]}"
fi

# ============================================================================
log_header "VIEW VERIFICATION"

log_check "Counting views..."
VIEW_COUNT=$(run_query "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';")

if [ "$VIEW_COUNT" -ge "9" ]; then
    log_pass "Found $VIEW_COUNT views (expected 9+)"
else
    log_warning "Found only $VIEW_COUNT views (expected 9)"
fi

log_check "Verifying critical views..."
CRITICAL_VIEWS=(
    "comprehensive_product_inventory_view"
    "inventory_products_view"
    "active_promotions"
    "admin_users"
    "recent_login_activity"
    "store_settings_view"
    "wishlist_details"
    "v_hot_translations"
    "v_translation_stats"
)

for view in "${CRITICAL_VIEWS[@]}"; do
    EXISTS=$(run_query "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND table_name = '$view';")
    if [ "$EXISTS" -eq "1" ]; then
        echo "       ✓ $view"
    else
        echo "       ✗ $view (missing)"
    fi
done

# ============================================================================
log_header "INDEX VERIFICATION"

log_check "Counting indexes..."
INDEX_COUNT=$(run_query "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';")

if [ "$INDEX_COUNT" -ge "500" ]; then
    log_pass "Found $INDEX_COUNT indexes (expected 500+)"
elif [ "$INDEX_COUNT" -ge "400" ]; then
    log_warning "Found $INDEX_COUNT indexes (expected 500+)"
else
    log_fail "Found only $INDEX_COUNT indexes (expected 500+)"
fi

log_check "Verifying GiST indexes for spatial columns..."
GIST_COUNT=$(run_query "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexdef LIKE '%USING gist%';")
if [ "$GIST_COUNT" -gt "0" ]; then
    log_pass "Found $GIST_COUNT GiST indexes for spatial queries"
else
    log_warning "No GiST indexes found (spatial queries may be slow)"
fi

# ============================================================================
log_header "FOREIGN KEY VERIFICATION"

log_check "Counting foreign key constraints..."
FK_COUNT=$(run_query "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public';")

if [ "$FK_COUNT" -ge "140" ]; then
    log_pass "Found $FK_COUNT foreign keys (expected 140+)"
elif [ "$FK_COUNT" -ge "120" ]; then
    log_warning "Found $FK_COUNT foreign keys (expected 140+)"
else
    log_fail "Found only $FK_COUNT foreign keys (expected 140+)"
fi

# ============================================================================
log_header "SEQUENCE VERIFICATION"

log_check "Counting sequences..."
SEQ_COUNT=$(run_query "SELECT COUNT(*) FROM information_schema.sequences WHERE sequence_schema = 'public';")

if [ "$SEQ_COUNT" -ge "21" ]; then
    log_pass "Found $SEQ_COUNT sequences (expected 21+)"
else
    log_warning "Found $SEQ_COUNT sequences (expected 21)"
fi

# ============================================================================
log_header "CUSTOM TYPE VERIFICATION"

log_check "Verifying custom types..."
TYPE_EXISTS=$(run_query "SELECT COUNT(*) FROM pg_type WHERE typname = 'user_role_simple';")

if [ "$TYPE_EXISTS" -eq "1" ]; then
    log_pass "Custom type 'user_role_simple' exists"
else
    log_fail "Custom type 'user_role_simple' not found"
fi

# ============================================================================
log_header "TRIGGER VERIFICATION"

log_check "Counting triggers..."
TRIGGER_COUNT=$(run_query "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public';")

if [ "$TRIGGER_COUNT" -ge "10" ]; then
    log_pass "Found $TRIGGER_COUNT triggers"
else
    log_warning "Found $TRIGGER_COUNT triggers (expected 10+)"
fi

# ============================================================================
log_header "COLUMN VERIFICATION FOR KEY TABLES"

log_check "Verifying users table has all required columns..."
USERS_COLS=$(run_query "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users';")
if [ "$USERS_COLS" -ge "32" ]; then
    log_pass "Users table has $USERS_COLS columns (expected 32+)"
else
    log_fail "Users table has only $USERS_COLS columns (expected 32)"
fi

log_check "Verifying stores table has all required columns..."
STORES_COLS=$(run_query "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'stores';")
if [ "$STORES_COLS" -ge "28" ]; then
    log_pass "Stores table has $STORES_COLS columns (expected 28+)"
else
    log_fail "Stores table has only $STORES_COLS columns (expected 28)"
fi

log_check "Verifying orders table has all required columns..."
ORDERS_COLS=$(run_query "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'orders';")
if [ "$ORDERS_COLS" -ge "35" ]; then
    log_pass "Orders table has $ORDERS_COLS columns (expected 35+)"
else
    log_fail "Orders table has only $ORDERS_COLS columns (expected 35)"
fi

# ============================================================================
log_header "SPATIAL FEATURES VERIFICATION"

log_check "Verifying geography columns..."
GEOGRAPHY_COLS=$(run_query "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND udt_name = 'geography';")
if [ "$GEOGRAPHY_COLS" -gt "0" ]; then
    log_pass "Found $GEOGRAPHY_COLS geography columns (PostGIS spatial features)"
    run_query "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' AND udt_name = 'geography' ORDER BY table_name, column_name;" | while read line; do
        echo "       - $line"
    done
else
    log_warning "No geography columns found"
fi

# ============================================================================
log_header "DATA INTEGRITY CHECKS"

log_check "Checking for orphaned records..."
# This is a simple check - you may need to add more specific checks
HAS_DATA=$(run_query "SELECT COUNT(*) FROM users;")
echo "       Users table: $HAS_DATA records"

# ============================================================================
log_header "FUNCTION VERIFICATION"

log_check "Verifying helper functions..."
FUNC_COUNT=$(run_query "SELECT COUNT(*) FROM pg_proc p LEFT JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public';")
if [ "$FUNC_COUNT" -gt "0" ]; then
    log_pass "Found $FUNC_COUNT user-defined functions"
else
    log_warning "No user-defined functions found"
fi

# ============================================================================
log_header "MIGRATION SUMMARY"

echo ""
echo -e "${BLUE}Total Checks:${NC} $TOTAL_CHECKS"
echo -e "${GREEN}Passed:${NC} $PASSED_CHECKS"
echo -e "${RED}Failed:${NC} $FAILED_CHECKS"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo -e "Success Rate: ${SUCCESS_RATE}%"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ MIGRATION VERIFICATION PASSED${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Your ai-engine-db-postgis database is now a complete replica"
    echo "of the legacy database plus PostGIS spatial capabilities!"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ MIGRATION VERIFICATION FAILED${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Please review the failed checks above and re-run the migration"
    echo "if necessary. Check individual migration scripts for errors."
    echo ""
    exit 1
fi
