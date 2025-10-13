-- ============================================================================
-- Stage 1: Create Missing Sequences
-- Description: Sequences must be created before tables that reference them
-- ============================================================================

-- Extract sequences from legacy database for new tables
-- These are needed for serial/identity columns

CREATE SEQUENCE IF NOT EXISTS agi_audit_aggregates_id_seq;
CREATE SEQUENCE IF NOT EXISTS agi_audit_alerts_id_seq;
CREATE SEQUENCE IF NOT EXISTS agi_audit_logs_id_seq;
CREATE SEQUENCE IF NOT EXISTS agi_rate_limit_buckets_id_seq;
CREATE SEQUENCE IF NOT EXISTS agi_rate_limit_rules_id_seq;
CREATE SEQUENCE IF NOT EXISTS agi_rate_limit_violations_id_seq;

-- Grant permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO weedgo;

SELECT 'Stage 1: Sequences created successfully' AS status;
