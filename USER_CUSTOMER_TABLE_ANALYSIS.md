# User, Customer, and Admin Tables Analysis

## Table Overview

### User-Related Tables
1. **users** (8 records) - Main authentication and user management table
2. **user_profiles** (0 records) - Session-based user preferences and behavior
3. **user_addresses** - User shipping/billing addresses
4. **user_sessions** - Active user sessions
5. **user_login_logs** - Authentication audit trail

### Customer-Related Tables
1. **customers** (10 records) - Customer business data and CRM information
2. **customer_profiles** (1 record) - AI/recommendation engine customer data
3. **customer_reviews** - Product reviews by customers
4. **customer_pricing_rules** - Custom pricing for specific customers

### Admin Tables
- No dedicated admin tables exist
- Admin users are stored in `users` table with role = 'super_admin' or 'tenant_admin'

## Data Duplication Issues Identified

### 1. **users** vs **customers** Tables
**Major Duplication Found:**
- Both tables store: email, first_name, last_name, phone, date_of_birth, marketing_consent
- 8 users have corresponding customer records (automatic creation via trigger)
- 2 customers exist without user_id (orphaned records)

**Purpose Overlap:**
- `users`: Authentication, authorization, session management
- `customers`: Business/CRM data, purchase history, loyalty

**Redundant Fields:**
```sql
Duplicated in both tables:
- email (users.email = customers.email)
- first_name, last_name
- phone
- date_of_birth
- marketing_consent/sms_consent
- active/is_active status
```

### 2. **user_profiles** vs **customer_profiles** Tables
**Different Purposes but Similar Data:**
- `user_profiles`: Session-based, temporary profiles for non-registered users
  - Uses session_id as primary identifier
  - Stores preferences, needs, experience_level
  - Currently EMPTY (0 records)

- `customer_profiles`: AI/recommendation data for registered customers
  - Uses customer_id (varchar) as primary key
  - Stores preferences, purchase_history
  - Only 1 record exists

**Overlap:** Both store preferences and purchase_history in JSONB format

### 3. **users.profile_id** Field
- Users table has a `profile_id` field that appears unused
- No foreign key relationship established
- Likely intended to link to user_profiles but not implemented

## Relationship Issues

### Trigger-Based Duplication
```sql
Trigger: create_customer_on_user_insert
- Automatically creates customer record when user is inserted/updated
- Causes data duplication between users and customers tables
```

### Orphaned Records
- 2 customers without user_id (testuser1757646101@example.com, verify1757646592@example.com)
- These appear to be test records or incomplete registrations

### Multiple Profile Systems
1. User-based profiling (users → user_profiles)
2. Customer-based profiling (customers → customer_profiles)
3. Session-based profiling (user_profiles using session_id)

## Recommendations

### Short-Term Fixes
1. **Remove Duplicate Fields**
   - Keep authentication data in `users`
   - Keep business/CRM data in `customers`
   - Remove: email, name, phone from customers (use JOIN with users)

2. **Clean Orphaned Records**
   - Delete or link the 2 customer records without user_id
   - Audit and clean customer_profiles

3. **Consolidate Profile Tables**
   - Merge user_profiles and customer_profiles
   - Use single profile table with user_id foreign key

### Long-Term Architecture

#### Option 1: Unified User Model
```
users (authentication + basic info)
  ↓
user_profiles (preferences, AI data)
  ↓
user_addresses (shipping/billing)
```
- Remove customers table entirely
- Move CRM fields to user_profiles

#### Option 2: Clear Separation
```
users (authentication only)
  ↓
customers (business entity) - 1:1 with users
  ↓
customer_profiles (AI/preferences)
```
- Remove ALL duplicate fields
- Use users.id as customers.user_id (enforced foreign key)
- Clear single source of truth for each field

### Database Normalization Issues

**Current Violations:**
- **1NF Violation**: JSONB fields storing arrays/objects (preferences, purchase_history)
- **2NF Violation**: Duplicate data across tables
- **3NF Violation**: Transitive dependencies (user → customer → profile)

**Suggested Schema:**
```sql
-- Core authentication
users (id, email, password_hash, role, tenant_id, created_at)

-- Customer data (1:1 with users)
customers (id, user_id, loyalty_points, customer_type, total_spent, order_count)

-- Shared profile data
profiles (id, user_id, first_name, last_name, phone, date_of_birth, preferences)

-- Addresses (1:many with users)
addresses (id, user_id, type, address, city, state, postal_code, is_primary)
```

## Impact Analysis

### Current Issues:
1. **Data Inconsistency Risk**: Updates might not propagate to all duplicate fields
2. **Storage Waste**: ~40% redundant data storage
3. **Query Complexity**: JOINs required to get complete user information
4. **Maintenance Overhead**: Multiple tables to update for user changes

### Benefits of Cleanup:
1. **Performance**: Fewer JOINs, smaller tables
2. **Consistency**: Single source of truth
3. **Maintainability**: Clear data ownership
4. **Scalability**: Easier to shard/partition

## Migration Strategy

### Phase 1: Audit (Week 1)
- Document all code dependencies
- Identify API endpoints using these tables
- Create data mapping document

### Phase 2: Schema Refactor (Week 2)
- Create new normalized schema
- Write migration scripts
- Test with sample data

### Phase 3: Code Updates (Week 3-4)
- Update models and DAOs
- Modify API endpoints
- Update frontend queries

### Phase 4: Data Migration (Week 5)
- Run migration in staging
- Validate data integrity
- Production migration with rollback plan

## Summary

The current schema has significant duplication between users/customers tables and confusion between profile systems. The automatic trigger creating customer records for every user causes unnecessary duplication. A refactoring is recommended to:

1. Eliminate duplicate fields
2. Establish clear table purposes
3. Implement proper foreign key relationships
4. Consolidate profile systems
5. Remove orphaned records

This will improve performance, reduce storage costs, and simplify maintenance.