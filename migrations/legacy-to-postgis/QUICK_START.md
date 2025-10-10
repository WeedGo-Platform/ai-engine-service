# Quick Start: Migration & Verification

## Prerequisites

**Docker must be running!** The migration requires the ai-engine-db-postgis container to be active.

---

## Step 1: Start Docker & Database

```bash
# 1. Start Docker Desktop (if not running)
# On macOS: Open Docker Desktop application

# 2. Verify Docker is running
docker ps

# 3. Start the ai-engine-db-postgis container
docker start ai-engine-db-postgis

# 4. Wait for database to be ready (5-10 seconds)
sleep 10

# 5. Verify database is accessible
docker exec ai-engine-db-postgis psql -U weedgo -d ai_engine -c "SELECT version();"
```

---

## Step 2: Run Migration

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/migrations/legacy-to-postgis

# Run the master migration script
./000_MASTER_MIGRATION.sh
```

**Expected output:**
- Database connection successful
- 13 migrations executed sequentially
- Progress indicator for each migration
- Automatic backup creation
- Success summary

**Duration:** ~30-60 seconds

---

## Step 3: Verify Migration

```bash
# Run comprehensive verification
./VERIFY_MIGRATION.sh
```

**Expected results:**
- ✓ 6 extensions installed
- ✓ 118+ tables created
- ✓ 9+ views created
- ✓ 500+ indexes created
- ✓ 140+ foreign keys created
- ✓ 21+ sequences created
- ✓ All critical tables verified
- ✓ Spatial features verified

---

## Step 4: Manual Verification (Optional)

```bash
# Connect to database
docker exec -it ai-engine-db-postgis psql -U weedgo -d ai_engine

# Run verification queries:

-- Count tables
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
-- Expected: 118

-- Count views
SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';
-- Expected: 9+

-- List extensions
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('postgis', 'postgis_topology', 'pg_trgm', 'unaccent', 'uuid-ossp', 'plpgsql')
ORDER BY extname;
-- Expected: 6 rows

-- Verify users table columns
SELECT COUNT(*) FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'users';
-- Expected: 32+

-- Verify stores table columns
SELECT COUNT(*) FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'stores';
-- Expected: 28+

-- Test a view
SELECT COUNT(*) FROM comprehensive_product_inventory_view;

-- Exit psql
\q
```

---

## Troubleshooting

### Issue: Docker daemon not running

```bash
# macOS: Open Docker Desktop application from Applications folder
open -a Docker

# Wait for Docker to start (check menu bar icon)
# Then retry from Step 1
```

### Issue: Container not found

```bash
# Check if container exists
docker ps -a | grep postgis

# If container exists but stopped, start it:
docker start ai-engine-db-postgis
```

### Issue: Port 5434 already in use

```bash
# Check what's using port 5434
lsof -i :5434

# Stop conflicting container
docker ps | grep 5434
docker stop <container-name>
```

### Issue: Permission denied

```bash
# Make scripts executable
chmod +x 000_MASTER_MIGRATION.sh
chmod +x VERIFY_MIGRATION.sh
```

### Issue: Migration fails midway

```bash
# Check the backup file created:
ls -lh ai_engine_backup_*.sql

# Restore from backup if needed:
docker exec -i ai-engine-db-postgis psql -U weedgo -d ai_engine < ai_engine_backup_YYYYMMDD_HHMMSS.sql

# Fix the issue and re-run migration
./000_MASTER_MIGRATION.sh
```

---

## What If Docker Is Not Available?

If you cannot start Docker, you can:

1. **Review the migration scripts** without executing them
2. **Use a different PostgreSQL instance** (change DB_HOST, DB_PORT in scripts)
3. **Schedule the migration** for when Docker is available

---

## Next Steps After Successful Migration

1. ✅ **Test your application** with the new database schema
2. ✅ **Run integration tests**
3. ✅ **Check application logs** for any schema-related errors
4. ✅ **Update application connection strings** if needed
5. ✅ **Monitor database performance**
6. ✅ **Consider running ANALYZE** to update statistics:
   ```sql
   ANALYZE VERBOSE;
   ```

---

## Migration Files Summary

- `000_MASTER_MIGRATION.sh` - Automated migration execution
- `VERIFY_MIGRATION.sh` - Comprehensive verification script
- `001-013_*.sql` - Individual migration scripts
- `README.md` - Detailed documentation
- `QUICK_START.md` - This file

**Total Size:** ~120 KB
**Execution Time:** 30-60 seconds
**Tables Added:** 94
**Views Added:** 7
**Indexes Added:** 438
**Foreign Keys Added:** 118

---

## Success Criteria

Migration is successful when:
- [x] All 13 migration scripts execute without errors
- [x] Verification script shows 100% success rate
- [x] All critical tables exist
- [x] All views are queryable
- [x] Foreign keys are properly established
- [x] PostGIS spatial features are available

---

**Need Help?** Review the detailed README.md or check individual migration script comments.
