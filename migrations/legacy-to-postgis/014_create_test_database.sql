-- ============================================================================
-- Migration: Create Test Database
-- Description: Create ai_engine_test database for testing
-- Dependencies: 013_create_views.sql
-- ============================================================================

-- Note: This script creates a separate test database
-- Run this as postgres superuser or with CREATEDB privilege

-- Create the test database if it doesn't exist
SELECT 'CREATE DATABASE ai_engine_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ai_engine_test')\gexec

-- Grant permissions to weedgo user
GRANT ALL PRIVILEGES ON DATABASE ai_engine_test TO weedgo;

-- Connect to test database and set up schema
\c ai_engine_test

-- The test database will inherit the same schema as the main database
-- You can run migrations 001-013 against ai_engine_test to create the schema

COMMENT ON DATABASE ai_engine_test IS 'Test database for ai-engine-service integration tests';

-- Create a schema_version table to track migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER
);

COMMENT ON TABLE schema_migrations IS 'Track applied database migrations';
