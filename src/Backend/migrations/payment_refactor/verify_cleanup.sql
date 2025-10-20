-- Verification Script: Payment Tables Cleanup
-- Purpose: Verify all orphaned tables are removed and only 6 core tables remain
-- Date: 2025-01-19

\echo '======================================================================='
\echo 'Payment Tables Cleanup Verification'
\echo '======================================================================='
\echo ''

-- ============================================================================
-- 1. Check Current Payment Tables (Should be exactly 6)
-- ============================================================================

\echo '1. CURRENT PAYMENT TABLES IN PUBLIC SCHEMA:'
\echo '   Expected: 6 tables (payment_providers, store_payment_providers,'
\echo '             payment_transactions, payment_methods, payment_refunds, payment_webhooks)'
\echo ''

SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'payment%'
    AND schemaname = 'public'
ORDER BY tablename;

\echo ''

-- ============================================================================
-- 2. Verify Orphaned Tables Are Gone (Should return 0 rows)
-- ============================================================================

\echo '2. CHECKING FOR ORPHANED TABLES (Should return 0 rows):'
\echo ''

SELECT
    tablename,
    'ORPHANED TABLE FOUND!' AS warning
FROM pg_tables
WHERE tablename IN (
    'payment_credentials',
    'payment_fee_splits',
    'payment_settlements',
    'payment_metrics',
    'payment_provider_health_metrics',
    'payment_subscriptions',
    'payment_disputes',
    'payment_webhook_routes',
    'payment_idempotency_keys',
    'payment_audit_log',
    'tenant_payment_providers'
)
AND schemaname = 'public';

\echo ''

-- ============================================================================
-- 3. Check Backup Schema (Should have 16 tables backed up)
-- ============================================================================

\echo '3. BACKUP SCHEMA (payment_backup):'
\echo '   Expected: All original tables backed up'
\echo ''

SELECT
    COUNT(*) AS backup_table_count,
    CASE
        WHEN COUNT(*) >= 10 THEN '✅ Backups exist'
        ELSE '⚠️  Backups missing!'
    END AS status
FROM pg_tables
WHERE schemaname = 'payment_backup';

\echo ''

SELECT tablename
FROM pg_tables
WHERE schemaname = 'payment_backup'
ORDER BY tablename;

\echo ''

-- ============================================================================
-- 4. Verify store_payment_providers Replaced tenant_payment_providers
-- ============================================================================

\echo '4. VERIFY STORE-LEVEL PROVIDER TABLE:'
\echo '   Checking store_payment_providers exists (replaces tenant_payment_providers)'
\echo ''

SELECT
    EXISTS(
        SELECT 1 FROM pg_tables
        WHERE tablename = 'store_payment_providers'
        AND schemaname = 'public'
    ) AS store_providers_exists,
    NOT EXISTS(
        SELECT 1 FROM pg_tables
        WHERE tablename = 'tenant_payment_providers'
        AND schemaname = 'public'
    ) AS tenant_providers_removed;

\echo ''

-- ============================================================================
-- 5. Check Column Counts (Verify simplification)
-- ============================================================================

\echo '5. COLUMN COUNTS (Verify schema simplification):'
\echo ''

SELECT
    table_name,
    COUNT(*) AS column_count,
    CASE table_name
        WHEN 'payment_providers' THEN '12 expected'
        WHEN 'store_payment_providers' THEN '11 expected'
        WHEN 'payment_transactions' THEN '17 expected (was 38)'
        WHEN 'payment_methods' THEN '14 expected'
        WHEN 'payment_refunds' THEN '12 expected'
        WHEN 'payment_webhooks' THEN '11 expected'
    END AS expected_count
FROM information_schema.columns
WHERE table_name IN (
    'payment_providers',
    'store_payment_providers',
    'payment_transactions',
    'payment_methods',
    'payment_refunds',
    'payment_webhooks'
)
AND table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

\echo ''

-- ============================================================================
-- 6. Check Provider Seeding
-- ============================================================================

\echo '6. PAYMENT PROVIDERS (Should have 3 seeded providers):'
\echo ''

SELECT
    provider_name,
    provider_type,
    is_active,
    priority,
    supported_currencies
FROM payment_providers
ORDER BY priority;

\echo ''

-- ============================================================================
-- 7. Verify Foreign Key Relationships
-- ============================================================================

\echo '7. FOREIGN KEY RELATIONSHIPS:'
\echo '   Checking all payment tables have proper FK constraints'
\echo ''

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name LIKE 'payment%'
ORDER BY tc.table_name, kcu.column_name;

\echo ''

-- ============================================================================
-- 8. Check Indexes
-- ============================================================================

\echo '8. INDEXES ON PAYMENT TABLES:'
\echo ''

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE 'payment%'
    AND schemaname = 'public'
ORDER BY tablename, indexname;

\echo ''

-- ============================================================================
-- Summary
-- ============================================================================

\echo '======================================================================='
\echo 'VERIFICATION SUMMARY'
\echo '======================================================================='
\echo ''

SELECT
    (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'payment%') AS current_payment_tables,
    (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'payment_backup') AS backup_tables,
    (SELECT COUNT(*) FROM payment_providers) AS providers_seeded,
    CASE
        WHEN (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'payment%') = 6
        AND NOT EXISTS(SELECT 1 FROM pg_tables WHERE tablename = 'tenant_payment_providers' AND schemaname = 'public')
        AND EXISTS(SELECT 1 FROM pg_tables WHERE tablename = 'store_payment_providers' AND schemaname = 'public')
        THEN '✅ CLEANUP COMPLETE'
        ELSE '⚠️  CLEANUP INCOMPLETE'
    END AS status;

\echo ''
\echo 'Expected Results:'
\echo '  - current_payment_tables: 6'
\echo '  - backup_tables: >= 10'
\echo '  - providers_seeded: 3'
\echo '  - status: ✅ CLEANUP COMPLETE'
\echo ''
\echo '======================================================================='
