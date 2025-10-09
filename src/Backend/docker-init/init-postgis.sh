#!/bin/sh
# Initialize PostGIS extension in the database

set -e

# Run as postgres user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create PostGIS extension
    CREATE EXTENSION IF NOT EXISTS postgis;

    -- Create PostGIS topology extension (optional but useful)
    CREATE EXTENSION IF NOT EXISTS postgis_topology;

    -- Verify installation
    SELECT PostGIS_version();
EOSQL

echo "PostGIS extension initialized successfully"
