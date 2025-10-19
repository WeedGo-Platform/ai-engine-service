#!/bin/bash

# Payment Refactor Migration Runner
# Purpose: Execute all payment refactor migrations in order
# Date: 2025-01-18

set -e  # Exit on error

# Database connection details
DB_HOST="localhost"
DB_PORT="5434"
DB_NAME="ai_engine"
DB_USER="weedgo"
DB_PASSWORD="weedgo123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Connection string
CONN_STRING="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Payment System Refactor Migration${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to run a migration
run_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file" .sql)

    echo -e "${YELLOW}Running: ${migration_name}${NC}"

    if psql "$CONN_STRING" -f "$migration_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${migration_name} completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ ${migration_name} FAILED${NC}"
        echo -e "${RED}Migration aborted. Check error logs above.${NC}"
        return 1
    fi
}

# Confirmation prompt
echo -e "${YELLOW}This will:${NC}"
echo "1. Backup all 16 existing payment tables"
echo "2. Drop 10 deprecated tables"
echo "3. Recreate 6 core tables with simplified schema"
echo "4. Seed 3 payment providers (Clover, Moneris, Interac)"
echo ""
echo -e "${YELLOW}Database:${NC} $DB_NAME @ $DB_HOST:$DB_PORT"
echo ""
read -p "Continue? (yes/no): " -n 3 -r
echo ""

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo -e "${RED}Migration cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Starting migrations...${NC}"
echo ""

# Run migrations in order
MIGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_migration "$MIGRATION_DIR/001_backup_payment_schema.sql" || exit 1
echo ""

run_migration "$MIGRATION_DIR/002_drop_deprecated_payment_tables.sql" || exit 1
echo ""

run_migration "$MIGRATION_DIR/003_recreate_payment_core_tables.sql" || exit 1
echo ""

run_migration "$MIGRATION_DIR/004_seed_payment_providers.sql" || exit 1
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All migrations completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Show summary
echo -e "${YELLOW}Summary:${NC}"
psql "$CONN_STRING" -c "
SELECT
    tablename,
    (SELECT COUNT(*)
     FROM information_schema.columns
     WHERE table_name = tablename
       AND table_schema = 'public') AS column_count
FROM pg_tables
WHERE tablename LIKE 'payment%'
  OR tablename LIKE '%payment%'
  AND schemaname = 'public'
ORDER BY tablename;
"

echo ""
echo -e "${YELLOW}Payment Providers:${NC}"
psql "$CONN_STRING" -c "
SELECT
    provider_name,
    provider_type,
    is_active,
    is_sandbox,
    priority
FROM payment_providers
ORDER BY priority;
"

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Review migration logs"
echo "2. Implement DDD domain models"
echo "3. Update provider integrations for store-level architecture"
echo "4. Implement V2 API endpoints"
echo ""
echo -e "${YELLOW}Rollback:${NC} If needed, run: psql \"$CONN_STRING\" -f 999_rollback.sql"
echo ""
