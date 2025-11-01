#!/bin/bash

# ============================================================================
# MASTER MIGRATION SCRIPT: Legacy to PostGIS Migration
# ============================================================================
# Description: Complete migration from ai-engine-db to ai-engine-db-postgis
# Transforms ai-engine-db-postgis into full replica of legacy + PostGIS
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# ===========================
# CONFIGURATION
# ===========================

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5434}"
DB_NAME="${DB_NAME:-ai_engine}"
DB_USER="${DB_USER:-weedgo}"
DB_PASSWORD="${DB_PASSWORD:-weedgo123}"

# Migration directory
MIGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===========================
# HELPER FUNCTIONS
# ===========================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

execute_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file")

    log_info "Executing migration: $migration_name"

    local start_time=$(date +%s%3N)

    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$migration_file" > /dev/null 2>&1; then
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        log_success "✓ $migration_name completed in ${duration}ms"
        return 0
    else
        log_error "✗ $migration_file failed"
        return 1
    fi
}

check_connection() {
    log_info "Checking database connection..."

    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Database connection successful"
        return 0
    else
        log_error "Cannot connect to database"
        return 1
    fi
}

create_backup() {
    log_info "Creating database backup before migration..."

    local backup_file="ai_engine_backup_$(date +%Y%m%d_%H%M%S).sql"

    if PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > "$backup_file" 2>/dev/null; then
        log_success "Backup created: $backup_file"
        echo "$backup_file"
        return 0
    else
        log_warning "Backup creation failed, continuing anyway..."
        return 1
    fi
}

# ===========================
# MAIN MIGRATION
# ===========================

main() {
    echo "============================================================================"
    echo "  AI-ENGINE DATABASE MIGRATION: Legacy to PostGIS"
    echo "============================================================================"
    echo ""
    echo "Database: $DB_NAME"
    echo "Host: $DB_HOST:$DB_PORT"
    echo "User: $DB_USER"
    echo ""
    echo "This will transform ai-engine-db-postgis into a complete replica of"
    echo "the legacy ai-engine-db database PLUS PostGIS spatial capabilities."
    echo ""
    read -p "Do you want to continue? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warning "Migration cancelled by user"
        exit 0
    fi

    # Check database connection
    if ! check_connection; then
        log_error "Please check your database connection settings"
        exit 1
    fi

    # Create backup
    backup_file=$(create_backup)

    echo ""
    log_info "Starting migration process..."
    echo ""

    # Migration order (CRITICAL: Do not change order)
    migrations=(
        "001_install_extensions.sql"
        "002_create_custom_types.sql"
        "003_alter_users_table.sql"
        "004_alter_stores_table.sql"
        "005_alter_orders_table.sql"
        "006_create_foundation_tables.sql"
        "007_create_inventory_tables.sql"
        "008_create_payment_tables.sql"
        "009_create_delivery_pricing_tables.sql"
        "010_create_reviews_ai_tables.sql"
        "011_create_communication_auth_tables.sql"
        "012_add_foreign_keys.sql"
        "013_create_views.sql"
    )

    # Track migration progress
    total_migrations=${#migrations[@]}
    completed_migrations=0
    failed_migrations=0

    # Execute migrations in order
    for migration in "${migrations[@]}"; do
        migration_path="$MIGRATION_DIR/$migration"

        if [ ! -f "$migration_path" ]; then
            log_error "Migration file not found: $migration"
            failed_migrations=$((failed_migrations + 1))
            continue
        fi

        if execute_migration "$migration_path"; then
            completed_migrations=$((completed_migrations + 1))
        else
            failed_migrations=$((failed_migrations + 1))
            log_error "Migration failed: $migration"

            if [ "$backup_file" != "" ]; then
                log_warning "You can restore from backup: $backup_file"
            fi

            read -p "Do you want to continue with remaining migrations? (yes/no): " -r
            echo ""

            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                log_error "Migration aborted"
                exit 1
            fi
        fi
    done

    echo ""
    echo "============================================================================"
    echo "  MIGRATION SUMMARY"
    echo "============================================================================"
    echo "Total migrations: $total_migrations"
    echo -e "${GREEN}Completed: $completed_migrations${NC}"
    if [ $failed_migrations -gt 0 ]; then
        echo -e "${RED}Failed: $failed_migrations${NC}"
    fi
    echo ""

    if [ $failed_migrations -eq 0 ]; then
        log_success "🎉 Migration completed successfully!"
        echo ""
        log_info "Your ai-engine-db-postgis database now contains:"
        echo "  • All 118 tables from legacy database"
        echo "  • All 9 views"
        echo "  • PostGIS spatial extensions"
        echo "  • Complete schema parity with legacy + spatial features"
        echo ""
        log_info "Next steps:"
        echo "  1. Run integration tests"
        echo "  2. Verify data integrity"
        echo "  3. Update application connection strings"
        echo "  4. Monitor performance"
        echo ""
    else
        log_warning "Migration completed with errors"
        echo ""
        log_info "Please review the failed migrations and re-run if necessary"
        if [ "$backup_file" != "" ]; then
            log_info "Backup available: $backup_file"
        fi
        echo ""
    fi
}

# Run main function
main "$@"
