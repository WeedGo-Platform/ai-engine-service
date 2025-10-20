-- Check all payment-related tables currently in database
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE tablename LIKE 'payment%' OR tablename LIKE '%payment%'
ORDER BY schemaname, tablename;
