-- ============================================================================
-- Migration: Install Missing Extensions
-- Description: Add pg_trgm and unaccent extensions to complement PostGIS
-- Dependencies: None
-- ============================================================================

-- Enable pg_trgm for fuzzy text search and trigram similarity
-- This is critical for product search, auto-suggest, and fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable unaccent for accent-insensitive text search
-- Important for multilingual cannabis product names
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Verify all extensions are installed
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('postgis', 'postgis_topology', 'pg_trgm', 'unaccent', 'uuid-ossp', 'plpgsql')
ORDER BY extname;

-- Expected result: 6 extensions
-- 1. pg_trgm
-- 2. plpgsql
-- 3. postgis
-- 4. postgis_topology
-- 5. unaccent
-- 6. uuid-ossp
