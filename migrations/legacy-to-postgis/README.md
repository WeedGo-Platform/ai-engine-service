# AI-Engine Database Migration: Legacy to PostGIS

## Overview

This migration transforms **ai-engine-db-postgis** from a minimal 24-table database into a **complete replica** of the legacy **ai-engine-db** (118 tables) **PLUS** PostGIS spatial capabilities.

### Migration Goals

✅ **Complete Schema Parity**: All 118 tables from legacy database
✅ **Spatial Enhancement**: Retain PostGIS extensions for location-based features
✅ **Zero Data Loss**: Preserve all existing data in ai-engine-db-postgis
✅ **Production Ready**: Full indexes, constraints, views, and triggers

---

## 🎯 What This Migration Adds

### Database Objects Added

| Category | Before | After | Added |
|----------|--------|-------|-------|
| **Tables** | 24 | 118 | +94 |
| **Views** | 2 | 9 | +7 |
| **Indexes** | 66 | 504 | +438 |
| **Foreign Keys** | 22 | 140 | +118 |
| **Sequences** | 4 | 21 | +17 |
| **Extensions** | 3 | 6 | +3 |

### Feature Categories

#### 🛍️ E-Commerce & Inventory (20 tables)
- OCS product catalog (5,388 products)
- Store-level inventory management
- Batch/lot tracking for recalls
- Purchase order management
- Shopping cart persistence
- Accessory catalog
- Shelf location management

#### 💳 Payment Processing (16 tables)
- Payment provider configuration
- Transaction processing
- Refund management
- Dispute/chargeback tracking
- Idempotency keys
- Webhook handling
- Payment analytics

#### 🚚 Delivery & Logistics (8 tables)
- Delivery zones with geofencing
- Real-time GPS tracking
- Route optimization
- Driver dispatch
- Order status history

#### 💰 Pricing & Promotions (9 tables)
- Dynamic pricing rules
- Customer-specific pricing (VIP/wholesale)
- Volume discounts (price tiers)
- Bundle deals
- Discount codes
- Promotion tracking
- Tax rate management

#### ⭐ Reviews & Ratings (5 tables)
- Customer product reviews
- Aggregate product ratings
- Review media (photos/videos)
- Helpfulness voting
- Review attributes

#### 🤖 AI & Machine Learning (15 tables)
- AI conversation tracking
- Chat interaction logs
- Model version control
- Model deployment management
- Training data management
- Product recommendations
- Conversion metrics

#### 📢 Communication & Marketing (11 tables)
- Broadcast campaigns
- Email/SMS/Push notifications
- Message templates
- Customer segmentation
- Communication preferences
- Unsubscribe management (CAN-SPAM)
- Communication analytics

#### 🌍 Translation & i18n (6 tables)
- Multi-language support
- Translation management
- Translation batches
- Store-specific overrides

#### 🔐 Authentication & Security (11 tables)
- Token management (access, refresh)
- Token blacklist
- API key management
- OTP/2FA support
- Voice biometric authentication
- Age verification logs
- Location access auditing

#### ⚙️ Foundation & Config (8 tables)
- Canadian provinces/territories
- Provincial suppliers (OCS, SQDC, etc.)
- User profiles
- User addresses
- System settings
- Store settings
- Holidays
- Role-based permissions (RBAC)

---

## 📋 Prerequisites

### Software Requirements
- PostgreSQL 16+ (ai-engine-db-postgis uses Postgres 17)
- psql command-line tool
- Bash shell (macOS/Linux)

### Database Requirements
- ai-engine-db-postgis container running on port 5434
- Database credentials:
  - Host: `localhost`
  - Port: `5434`
  - Database: `ai_engine`
  - User: `weedgo`
  - Password: `weedgo123`

### Permissions Required
- CREATE EXTENSION
- CREATE TABLE
- ALTER TABLE
- CREATE INDEX
- CREATE VIEW
- CREATE TRIGGER

---

## 🚀 Migration Execution

### Option 1: Automated Migration (Recommended)

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/migrations/legacy-to-postgis

# Run the master migration script
./000_MASTER_MIGRATION.sh
```

**Features:**
- ✅ Automatic backup creation
- ✅ Progress tracking
- ✅ Error handling
- ✅ Rollback guidance
- ✅ Execution timing
- ✅ Migration summary

### Option 2: Manual Migration

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5434
export DB_USER=weedgo
export DB_PASSWORD=weedgo123
export DB_NAME=ai_engine

# Execute migrations in order
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 001_install_extensions.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 002_create_custom_types.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 003_alter_users_table.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 004_alter_stores_table.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 005_alter_orders_table.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 006_create_foundation_tables.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 007_create_inventory_tables.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 008_create_payment_tables.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 009_create_delivery_pricing_tables.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 010_create_reviews_ai_tables.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 011_create_communication_auth_tables.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 012_add_foreign_keys.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 013_create_views.sql
```

---

## 📁 Migration Files

### Core Migrations (Sequential Order)

1. **001_install_extensions.sql**
   - Installs `pg_trgm` for fuzzy text search
   - Installs `unaccent` for accent-insensitive search
   - Verifies all 6 extensions are present

2. **002_create_custom_types.sql**
   - Creates `user_role_simple` enum
   - Creates `update_updated_at_column()` trigger function
   - Creates helper functions

3. **003_alter_users_table.sql**
   - Adds 18 missing columns to users table
   - Converts role column to enum type
   - Adds missing indexes and constraints

4. **004_alter_stores_table.sql**
   - Adds 22 missing columns to stores table
   - Adds location fields (latitude, longitude)
   - Adds POS and license tracking

5. **005_alter_orders_table.sql**
   - Adds 18 missing columns to orders table
   - Adds POS transaction support
   - Adds delivery type and promo code fields

6. **006_create_foundation_tables.sql**
   - Creates provinces_territories
   - Creates provincial_suppliers
   - Creates profiles
   - Creates user_addresses
   - Creates system_settings
   - Creates store_settings
   - Creates holidays
   - Creates role_permissions

7. **007_create_inventory_tables.sql**
   - Creates OCS product catalog
   - Creates OCS inventory system
   - Creates batch tracking
   - Creates purchase orders
   - Creates cart sessions
   - Creates accessories catalog

8. **008_create_payment_tables.sql**
   - Creates payment providers
   - Creates payment transactions
   - Creates payment refunds
   - Creates payment disputes
   - Creates payment webhooks
   - Creates payment audit logging

9. **009_create_delivery_pricing_tables.sql**
   - Creates delivery zones (with PostGIS geometry)
   - Creates delivery tracking
   - Creates pricing rules
   - Creates discount codes
   - Creates tax rates

10. **010_create_reviews_ai_tables.sql**
    - Creates customer reviews
    - Creates product ratings
    - Creates wishlist
    - Creates AI conversations
    - Creates chat interactions
    - Creates ML model management

11. **011_create_communication_auth_tables.sql**
    - Creates broadcast campaigns
    - Creates communication logs
    - Creates message templates
    - Creates translations
    - Creates auth tokens
    - Creates API keys
    - Creates OTP codes
    - Creates voice authentication

12. **012_add_foreign_keys.sql**
    - Adds cross-table foreign key constraints
    - Adds composite indexes
    - Adds triggers for updated_at

13. **013_create_views.sql**
    - Creates comprehensive_product_inventory_view
    - Creates inventory_products_view
    - Creates active_promotions
    - Creates admin_users
    - Creates wishlist_details
    - Creates translation views

14. **014_create_test_database.sql**
    - Creates ai_engine_test database
    - Sets up schema_migrations tracking

---

## ✅ Post-Migration Verification

### 1. Verify Table Count

```sql
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
-- Expected: 118 tables
```

### 2. Verify Extensions

```sql
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('postgis', 'postgis_topology', 'pg_trgm', 'unaccent', 'uuid-ossp', 'plpgsql')
ORDER BY extname;
-- Expected: 6 rows
```

### 3. Verify Views

```sql
SELECT COUNT(*) FROM information_schema.views
WHERE table_schema = 'public';
-- Expected: 9 views (or more if PostGIS adds views)
```

### 4. Verify Foreign Keys

```sql
SELECT COUNT(*) FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public';
-- Expected: 140+ foreign keys
```

### 5. Test Key Views

```sql
-- Test comprehensive inventory view
SELECT COUNT(*) FROM comprehensive_product_inventory_view;

-- Test active promotions
SELECT COUNT(*) FROM active_promotions;

-- Test admin users
SELECT COUNT(*) FROM admin_users;
```

---

## 🔄 Rollback Procedure

If migration fails, you can restore from the automatic backup:

```bash
# The migration script creates a backup file: ai_engine_backup_YYYYMMDD_HHMMSS.sql

# Restore from backup
psql -h localhost -p 5434 -U weedgo -d ai_engine < ai_engine_backup_20250109_143000.sql
```

---

## ⚠️ Important Notes

### Critical Constraints
1. **Cannabis Compliance**: Age verification, license tracking, batch/lot numbers
2. **Payment Security**: Idempotency keys prevent duplicate charges
3. **Privacy Compliance**: Location access logging, unsubscribe management
4. **Spatial Data**: PostGIS columns for delivery zones, store locations, tracking

### Performance Considerations
- 504 indexes created for query optimization
- GiST indexes on geography columns for spatial queries
- Partial indexes for filtered queries
- Triggers on updated_at columns may add overhead

### Data Migration
This migration creates the **schema only**. To migrate data from the legacy database:

```bash
# Export data from legacy database
pg_dump -h localhost -p 5434 -U weedgo -d ai_engine \
  --data-only --inserts --disable-triggers \
  -t table_name > data.sql

# Import into new database
psql -h localhost -p 5434 -U weedgo -d ai_engine < data.sql
```

---

## 📊 Migration Statistics

| Metric | Value |
|--------|-------|
| Migration Files | 14 |
| Tables Created | 94 |
| Tables Altered | 3 |
| Columns Added | 58 |
| Views Created | 7 |
| Indexes Added | 438 |
| Foreign Keys Added | 118 |
| Extensions Added | 3 |
| Custom Types Created | 1 |
| Triggers Added | 10+ |
| Estimated Execution Time | 30-60 seconds |
| Backup Size (empty DB) | ~1-2 MB |

---

## 🐛 Troubleshooting

### Issue: Permission Denied
```
ERROR: permission denied to create extension
```
**Solution**: Run as postgres superuser or grant permissions:
```sql
ALTER USER weedgo WITH SUPERUSER;
```

### Issue: Extension Not Found
```
ERROR: could not open extension control file
```
**Solution**: Install PostgreSQL contrib packages:
```bash
# macOS
brew install postgis

# Ubuntu/Debian
apt-get install postgresql-17-postgis-3
```

### Issue: Port Already in Use
```
Error: port 5434 already allocated
```
**Solution**: Stop conflicting container or change port in script

### Issue: Out of Memory
```
ERROR: out of memory
```
**Solution**: Increase Docker memory limit or PostgreSQL `shared_buffers`

---

## 📞 Support

For issues or questions:
- Check the gap analysis report
- Review individual migration file comments
- Consult PostgreSQL and PostGIS documentation

---

## 📝 License & Credits

Created as part of the WeedGo microservices suite.
Migration designed to preserve full legacy functionality while adding spatial capabilities.

---

**Last Updated**: 2025-01-09
**Migration Version**: 1.0.0
**Compatible With**: PostgreSQL 16+, PostGIS 3.5+
