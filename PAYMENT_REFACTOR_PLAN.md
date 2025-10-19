# Payment System Refactoring Plan
## Store-Level Providers + DDD Architecture + Simplified Schema

**Status:** Planning Phase
**Created:** 2025-01-18
**Objective:** Refactor payment system to use store-level providers, complete DDD implementation, remove V1 APIs, and simplify database schema from 16 to 6 essential tables.

---

## Executive Summary

### Current State
- **16 payment database tables** (over-engineered for cannabis retail POS)
- **0 payment transactions** in database (clean slate for migration)
- **0 payment providers** configured (system never initialized)
- **Dual architecture**: V1 legacy API + partial V2 DDD implementation
- **Tenant-level providers** (incorrect granularity)
- **Fee structure complexity** (unnecessary for transaction processing)
- **5 providers defined** (Clover, Moneris, Interac, Nuvei, PayBright - only first 3 implemented)

### Target State
- **6 payment database tables** (essential only)
- **Store-level providers** (correct granularity for multi-location retail)
- **Complete DDD implementation** (V2 only)
- **3 providers** (Clover, Moneris, Interac)
- **No fee structure** (fees tracked by processors, not our system)
- **Simplified transaction model** (remove 21 unnecessary columns)

### Benefits
✅ **Reduced complexity**: 62.5% fewer tables (16 → 6)
✅ **Better architecture**: Store-level granularity matches real-world retail
✅ **Cleaner codebase**: Remove 7 V1 endpoint files + deprecated services
✅ **Faster development**: Focus on 3 providers instead of 5
✅ **Lower maintenance**: Single DDD architecture instead of dual systems
✅ **Simpler transactions**: 17 essential columns instead of 38

---

## Phase 1: Database Schema Migration

### 1.1 Tables to KEEP (6 tables)

#### ✅ `payment_providers` (Global Provider Registry)
**Purpose:** Master registry of payment processors
**Changes Required:**
- Remove fee-related columns: `fee_structure`, `settlement_schedule`
- Remove Nuvei and PayBright provider types from enum/validation
- Keep: `id`, `provider_name`, `provider_type`, `is_active`, `is_sandbox`, `configuration`, `capabilities`

```sql
-- Simplified schema (19 columns → 12 columns)
CREATE TABLE payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL, -- 'clover', 'moneris', 'interac'
    name VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_sandbox BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 100,
    supported_currencies TEXT[] DEFAULT '{CAD}',
    supported_payment_methods TEXT[] DEFAULT '{}',
    supported_card_types TEXT[] DEFAULT ARRAY['visa', 'mastercard', 'amex'],
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    webhook_url TEXT,
    rate_limits JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### ✅ `store_payment_providers` (Store-Level Provider Config) **[NEW TABLE]**
**Purpose:** Store-specific payment provider configurations
**Replaces:** `tenant_payment_providers` (renamed + refactored)
**Key Change:** `tenant_id` → `store_id`

```sql
CREATE TABLE store_payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) NOT NULL,
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    credentials_encrypted TEXT, -- Merged from payment_credentials table
    encryption_metadata JSONB NOT NULL,
    configuration JSONB DEFAULT '{}',
    oauth_tokens JSONB, -- For Clover OAuth
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,

    UNIQUE(store_id, provider_id)
);
CREATE INDEX idx_store_providers_active ON store_payment_providers(store_id, is_active);
CREATE INDEX idx_store_providers_default ON store_payment_providers(is_default) WHERE is_default = true;
```

#### ✅ `payment_transactions` (Core Transaction Log)
**Purpose:** Record of all payment attempts
**Changes Required:**
- **Remove 21 columns** related to fees, tenant-level data, and over-engineering
- **Add store-level references**
- **Simplify to essential transaction data**

```sql
-- Simplified schema (38 columns → 17 columns)
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_reference VARCHAR(100) UNIQUE NOT NULL,

    -- Relationships
    store_id UUID REFERENCES stores(id) NOT NULL,
    order_id UUID REFERENCES orders(id),
    user_id UUID REFERENCES users(id),
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,
    store_provider_id UUID REFERENCES store_payment_providers(id) NOT NULL,
    payment_method_id UUID REFERENCES payment_methods(id),

    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL, -- 'charge', 'authorize', 'capture'
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'

    -- Provider response
    provider_transaction_id VARCHAR(255),
    provider_response JSONB,
    error_code VARCHAR(100),
    error_message TEXT,

    -- Security & fraud prevention
    idempotency_key VARCHAR(255) UNIQUE,
    ip_address INET,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_payment_transactions_store_created ON payment_transactions(store_id, created_at DESC);
CREATE INDEX idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX idx_payment_transactions_provider_ref ON payment_transactions(provider_transaction_id, provider_id);
CREATE INDEX idx_payment_transactions_idempotency ON payment_transactions(idempotency_key) WHERE idempotency_key IS NOT NULL;
```

**Columns REMOVED (21):**
- `provider_fee` - Not needed for transaction processing
- `platform_fee` - Not needed for transaction processing
- `net_amount` - Not needed for transaction processing
- `tenant_net_amount` - Not needed for transaction processing
- `tax_amount` - Should be in order, not payment
- `tenant_id` - Redundant (store already references tenant)
- `tenant_provider_id` - Replaced by store_provider_id
- `fraud_status` - Over-engineering (use status instead)
- `risk_score` - Over-engineering for 3 providers
- `risk_factors` - Over-engineering
- `device_fingerprint` - Over-engineering
- `user_agent` - Not essential
- `authentication_status` - Over-engineering
- `authentication_data` - Over-engineering
- `processed_at` - Redundant with completed_at
- `failed_at` - Can be determined from status + updated_at
- `type` - Duplicate of transaction_type

#### ✅ `payment_methods` (Tokenized Customer Payment Methods)
**Purpose:** Store customer payment tokens (PCI compliant)
**Changes Required:**
- Remove `tenant_id` (use store_id only)
- Clean up duplicate columns (`payment_type` vs `type`, `token` vs `payment_token`, `card_last4` vs `card_last_four`)
- Remove `display_name` (can be generated client-side)

```sql
-- Simplified schema (22 columns → 14 columns)
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    store_id UUID REFERENCES stores(id),
    provider_id UUID REFERENCES payment_providers(id),

    -- Payment type & token
    type VARCHAR(50) NOT NULL, -- 'card', 'interac'
    payment_token TEXT NOT NULL, -- Provider's token (NOT raw card number)

    -- Display information (for UI only)
    card_last4 VARCHAR(4),
    card_brand VARCHAR(50), -- 'visa', 'mastercard', 'amex'
    card_exp_month INTEGER,
    card_exp_year INTEGER,

    -- Settings
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,

    -- Billing
    billing_address JSONB,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE INDEX idx_payment_methods_user ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_default ON payment_methods(user_id, is_default);
CREATE UNIQUE INDEX idx_payment_methods_token ON payment_methods(store_id, payment_token, provider_id) WHERE store_id IS NOT NULL;
```

**Columns REMOVED (8):**
- `payment_type` - Duplicate of `type`
- `token` - Duplicate of `payment_token`
- `card_last_four` - Duplicate of `card_last4`
- `display_name` - Can be generated client-side
- `tenant_id` - Not needed with store-level architecture

#### ✅ `payment_refunds`
**Purpose:** Track refund requests and processing
**Changes Required:**
- Clean up duplicate columns (`refund_amount` vs `amount`, `refund_reason` vs `reason`)
- Simplify approval tracking (single `created_by` instead of `requested_by`, `approved_by`, `initiated_by`)

```sql
-- Simplified schema (17 columns → 12 columns)
CREATE TABLE payment_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES payment_transactions(id) NOT NULL,
    refund_reference VARCHAR(100) UNIQUE NOT NULL,

    -- Refund details
    amount NUMERIC(10,2) NOT NULL,
    reason TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'

    -- Provider response
    provider_refund_id VARCHAR(255),
    provider_response JSONB,
    error_message TEXT,

    -- Tracking
    created_by UUID REFERENCES users(id),
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_payment_refunds_transaction ON payment_refunds(transaction_id);
CREATE INDEX idx_payment_refunds_status ON payment_refunds(status);
CREATE INDEX idx_payment_refunds_created ON payment_refunds(created_at DESC);
```

**Columns REMOVED (5):**
- `refund_amount` - Duplicate of `amount`
- `refund_reason` - Duplicate of `reason`
- `requested_by` - Merged into `created_by`
- `approved_by` - Over-engineering (use notes field)
- `initiated_by` - Duplicate of `created_by`
- `refund_transaction_id` - Unnecessary complexity

#### ✅ `payment_webhooks` (Webhook Event Log)
**Purpose:** Log incoming webhook events from providers
**Changes Required:**
- Clean up duplicate columns
- Remove over-engineering columns

```sql
-- Simplified schema (16 columns → 11 columns)
CREATE TABLE payment_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255), -- Provider's event ID
    webhook_id VARCHAR(255), -- Provider's webhook ID (if different)

    -- Payload
    payload JSONB NOT NULL,
    signature VARCHAR(500),
    is_verified BOOLEAN DEFAULT false,

    -- Processing status
    is_processed BOOLEAN DEFAULT false,
    processing_attempts INTEGER DEFAULT 0,
    processing_error TEXT,

    -- Timestamps
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_payment_webhooks_provider ON payment_webhooks(provider_id, received_at DESC);
CREATE INDEX idx_payment_webhooks_processed ON payment_webhooks(is_processed, received_at);
CREATE INDEX idx_payment_webhooks_type ON payment_webhooks(event_type);
```

**Columns REMOVED (5):**
- `created_at` - Duplicate of `received_at`
- `processed` - Duplicate of `is_processed`
- `signature_verified` - Duplicate of `is_verified`
- `error_message` - Duplicate of `processing_error`

---

### 1.2 Tables to REMOVE (10 tables)

#### ❌ `payment_fee_splits` (19 columns)
**Reason:** Fee structure removed - not needed for transaction processing
**Foreign Keys:** References `payment_transactions`, `tenants`
**Impact:** Simplifies revenue tracking, can be added later if needed

#### ❌ `payment_settlements`
**Reason:** Fee structure removed - settlements handled by payment processors
**Foreign Keys:** References `payment_providers`, `payment_fee_splits`
**Impact:** Reduces complexity, processors handle their own settlements

#### ❌ `payment_metrics`
**Reason:** Can be calculated from `payment_transactions` via analytics queries
**Foreign Keys:** References `payment_providers`, `tenants`, `stores`
**Impact:** Removes pre-computed metrics, use real-time queries instead

#### ❌ `payment_provider_health_metrics`
**Reason:** Over-engineering for 3 providers - manual monitoring is sufficient
**Foreign Keys:** References `payment_providers`
**Impact:** Simplifies monitoring, use application logs instead

#### ❌ `payment_subscriptions`
**Reason:** Cannabis retail doesn't use subscription billing
**Foreign Keys:** References `payment_providers`, `payment_methods`, `users`
**Impact:** Removes unused feature

#### ❌ `payment_disputes`
**Reason:** Can be handled via `payment_transactions` status field
**Foreign Keys:** References `payment_transactions`, `payment_providers`
**Impact:** Simplifies dispute tracking, use transaction notes/metadata instead

#### ❌ `payment_webhook_routes`
**Reason:** Routes can be stored in provider configuration JSONB
**Foreign Keys:** References `payment_providers`
**Impact:** Simplifies webhook routing

#### ❌ `payment_idempotency_keys`
**Reason:** Idempotency key is already a column in `payment_transactions`
**Foreign Keys:** References `payment_transactions`
**Impact:** Removes redundant table

#### ❌ `payment_audit_log`
**Reason:** Application logging + `payment_transactions` + `payment_webhooks` sufficient
**Foreign Keys:** References `payment_transactions`, `users`
**Impact:** Simplifies audit trail, use structured logs instead

#### ❌ `payment_credentials`
**Reason:** Credentials merged into `store_payment_providers` table
**Foreign Keys:** References `payment_providers`, `stores`, `tenants`, `users`
**Impact:** Consolidates provider configuration into single table

#### ❌ `tenant_payment_providers`
**Reason:** Replaced by `store_payment_providers` (store-level instead of tenant-level)
**Foreign Keys:** References `tenants`
**Impact:** Enables store-specific payment configurations

---

### 1.3 Migration Scripts

#### Migration Script 1: Backup Current Schema
```sql
-- migrations/001_backup_payment_schema.sql

-- Backup existing tables (even though they're empty)
CREATE TABLE _backup_payment_transactions AS SELECT * FROM payment_transactions;
CREATE TABLE _backup_payment_providers AS SELECT * FROM payment_providers;
CREATE TABLE _backup_payment_methods AS SELECT * FROM payment_methods;
CREATE TABLE _backup_tenant_payment_providers AS SELECT * FROM tenant_payment_providers;
CREATE TABLE _backup_payment_refunds AS SELECT * FROM payment_refunds;
CREATE TABLE _backup_payment_webhooks AS SELECT * FROM payment_webhooks;

-- Log migration start
INSERT INTO migration_log (migration_name, status, started_at)
VALUES ('001_backup_payment_schema', 'completed', NOW());
```

#### Migration Script 2: Drop Deprecated Tables
```sql
-- migrations/002_drop_deprecated_payment_tables.sql

BEGIN;

-- Drop tables in dependency order (children first)
DROP TABLE IF EXISTS payment_fee_splits CASCADE;
DROP TABLE IF EXISTS payment_settlements CASCADE;
DROP TABLE IF EXISTS payment_metrics CASCADE;
DROP TABLE IF EXISTS payment_provider_health_metrics CASCADE;
DROP TABLE IF EXISTS payment_subscriptions CASCADE;
DROP TABLE IF EXISTS payment_disputes CASCADE;
DROP TABLE IF EXISTS payment_webhook_routes CASCADE;
DROP TABLE IF EXISTS payment_idempotency_keys CASCADE;
DROP TABLE IF EXISTS payment_audit_log CASCADE;
DROP TABLE IF EXISTS payment_credentials CASCADE;

-- Log migration
INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('002_drop_deprecated_payment_tables', 'completed', NOW(), NOW());

COMMIT;
```

#### Migration Script 3: Recreate Core Tables with Simplified Schema
```sql
-- migrations/003_recreate_payment_core_tables.sql

BEGIN;

-- Drop existing tables (we have backups)
DROP TABLE IF EXISTS payment_refunds CASCADE;
DROP TABLE IF EXISTS payment_transactions CASCADE;
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS payment_webhooks CASCADE;
DROP TABLE IF EXISTS tenant_payment_providers CASCADE;
DROP TABLE IF EXISTS payment_providers CASCADE;

-- Recreate with simplified schemas (see section 1.1 for full schemas)

-- 1. payment_providers (simplified)
CREATE TABLE payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL CHECK (provider_type IN ('clover', 'moneris', 'interac')),
    name VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_sandbox BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 100,
    supported_currencies TEXT[] DEFAULT '{CAD}',
    supported_payment_methods TEXT[] DEFAULT '{}',
    supported_card_types TEXT[] DEFAULT ARRAY['visa', 'mastercard', 'amex'],
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    webhook_url TEXT,
    rate_limits JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_payment_providers_active ON payment_providers(is_active, priority);

-- 2. store_payment_providers (NEW - replaces tenant_payment_providers)
CREATE TABLE store_payment_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) NOT NULL,
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    credentials_encrypted TEXT,
    encryption_metadata JSONB NOT NULL DEFAULT '{}',
    configuration JSONB DEFAULT '{}',
    oauth_tokens JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    UNIQUE(store_id, provider_id)
);
CREATE INDEX idx_store_providers_active ON store_payment_providers(store_id, is_active);
CREATE INDEX idx_store_providers_default ON store_payment_providers(is_default) WHERE is_default = true;

-- 3. payment_transactions (simplified from 38 to 17 columns)
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_reference VARCHAR(100) UNIQUE NOT NULL,
    store_id UUID REFERENCES stores(id) NOT NULL,
    order_id UUID REFERENCES orders(id),
    user_id UUID REFERENCES users(id),
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,
    store_provider_id UUID REFERENCES store_payment_providers(id) NOT NULL,
    payment_method_id UUID REFERENCES payment_methods(id),
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('charge', 'authorize', 'capture', 'void')),
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded', 'voided')),
    provider_transaction_id VARCHAR(255),
    provider_response JSONB,
    error_code VARCHAR(100),
    error_message TEXT,
    idempotency_key VARCHAR(255) UNIQUE,
    ip_address INET,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX idx_payment_transactions_store_created ON payment_transactions(store_id, created_at DESC);
CREATE INDEX idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX idx_payment_transactions_provider_ref ON payment_transactions(provider_transaction_id, provider_id);
CREATE INDEX idx_payment_transactions_idempotency ON payment_transactions(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- 4. payment_methods (simplified from 22 to 14 columns)
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    store_id UUID REFERENCES stores(id),
    provider_id UUID REFERENCES payment_providers(id),
    type VARCHAR(50) NOT NULL CHECK (type IN ('card', 'interac')),
    payment_token TEXT NOT NULL,
    card_last4 VARCHAR(4),
    card_brand VARCHAR(50),
    card_exp_month INTEGER CHECK (card_exp_month BETWEEN 1 AND 12),
    card_exp_year INTEGER CHECK (card_exp_year >= 2025),
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    billing_address JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);
CREATE INDEX idx_payment_methods_user ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_default ON payment_methods(user_id, is_default);
CREATE UNIQUE INDEX idx_payment_methods_token ON payment_methods(store_id, payment_token, provider_id) WHERE store_id IS NOT NULL;

-- 5. payment_refunds (simplified from 17 to 12 columns)
CREATE TABLE payment_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES payment_transactions(id) NOT NULL,
    refund_reference VARCHAR(100) UNIQUE NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    reason TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    provider_refund_id VARCHAR(255),
    provider_response JSONB,
    error_message TEXT,
    created_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX idx_payment_refunds_transaction ON payment_refunds(transaction_id);
CREATE INDEX idx_payment_refunds_status ON payment_refunds(status);
CREATE INDEX idx_payment_refunds_created ON payment_refunds(created_at DESC);

-- 6. payment_webhooks (simplified from 16 to 11 columns)
CREATE TABLE payment_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES payment_providers(id) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255),
    webhook_id VARCHAR(255),
    payload JSONB NOT NULL,
    signature VARCHAR(500),
    is_verified BOOLEAN DEFAULT false,
    is_processed BOOLEAN DEFAULT false,
    processing_attempts INTEGER DEFAULT 0,
    processing_error TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
CREATE INDEX idx_payment_webhooks_provider ON payment_webhooks(provider_id, received_at DESC);
CREATE INDEX idx_payment_webhooks_processed ON payment_webhooks(is_processed, received_at);
CREATE INDEX idx_payment_webhooks_type ON payment_webhooks(event_type);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_payment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_payment_providers_updated_at BEFORE UPDATE ON payment_providers
    FOR EACH ROW EXECUTE FUNCTION update_payment_updated_at();
CREATE TRIGGER update_store_payment_providers_updated_at BEFORE UPDATE ON store_payment_providers
    FOR EACH ROW EXECUTE FUNCTION update_payment_updated_at();
CREATE TRIGGER update_payment_transactions_updated_at BEFORE UPDATE ON payment_transactions
    FOR EACH ROW EXECUTE FUNCTION update_payment_updated_at();
CREATE TRIGGER update_payment_methods_updated_at BEFORE UPDATE ON payment_methods
    FOR EACH ROW EXECUTE FUNCTION update_payment_updated_at();

-- Log migration
INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('003_recreate_payment_core_tables', 'completed', NOW(), NOW());

COMMIT;
```

#### Migration Script 4: Seed Payment Providers
```sql
-- migrations/004_seed_payment_providers.sql

BEGIN;

-- Insert Clover provider
INSERT INTO payment_providers (
    id,
    provider_name,
    provider_type,
    name,
    is_active,
    is_sandbox,
    priority,
    supported_currencies,
    supported_payment_methods,
    supported_card_types,
    configuration,
    capabilities,
    webhook_url
) VALUES (
    gen_random_uuid(),
    'Clover',
    'clover',
    'clover',
    true,
    true,
    1,
    ARRAY['CAD', 'USD'],
    ARRAY['card', 'contactless'],
    ARRAY['visa', 'mastercard', 'amex', 'discover'],
    '{"api_url": "https://sandbox.dev.clover.com", "oauth_url": "https://sandbox.dev.clover.com/oauth"}'::JSONB,
    '{"tokenization": true, "refunds": true, "partial_refunds": true, "void": true, "capture": true, "preauth": true}'::JSONB,
    '/api/v2/payments/webhooks/clover'
);

-- Insert Moneris provider
INSERT INTO payment_providers (
    id,
    provider_name,
    provider_type,
    name,
    is_active,
    is_sandbox,
    priority,
    supported_currencies,
    supported_payment_methods,
    supported_card_types,
    configuration,
    capabilities,
    webhook_url
) VALUES (
    gen_random_uuid(),
    'Moneris',
    'moneris',
    'moneris',
    true,
    true,
    2,
    ARRAY['CAD'],
    ARRAY['card', 'interac_debit'],
    ARRAY['visa', 'mastercard', 'amex'],
    '{"api_url": "https://esqa.moneris.com/gateway2/servlet/MpgRequest", "hosted_tokenization_url": "https://esqa.moneris.com/HPPtoken/index.php"}'::JSONB,
    '{"tokenization": true, "refunds": true, "partial_refunds": true, "void": true, "capture": true, "preauth": true, "interac": true}'::JSONB,
    '/api/v2/payments/webhooks/moneris'
);

-- Insert Interac provider
INSERT INTO payment_providers (
    id,
    provider_name,
    provider_type,
    name,
    is_active,
    is_sandbox,
    priority,
    supported_currencies,
    supported_payment_methods,
    supported_card_types,
    configuration,
    capabilities,
    webhook_url
) VALUES (
    gen_random_uuid(),
    'Interac',
    'interac',
    'interac',
    true,
    true,
    3,
    ARRAY['CAD'],
    ARRAY['interac_etransfer', 'interac_debit'],
    ARRAY[],
    '{"api_url": "https://gateway-sandbox.interac.ca", "etransfer_enabled": true}'::JSONB,
    '{"etransfer": true, "debit": true, "refunds": true, "notifications": true}'::JSONB,
    '/api/v2/payments/webhooks/interac'
);

-- Log migration
INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('004_seed_payment_providers', 'completed', NOW(), NOW());

COMMIT;
```

---

## Phase 2: DDD Domain Model Design

### 2.1 Domain Structure

```
Backend/
└── ddd_refactored/
    └── domain/
        └── payment_processing/
            ├── __init__.py
            ├── entities/
            │   ├── __init__.py
            │   ├── payment_transaction.py       # Aggregate Root
            │   ├── payment_method.py            # Entity
            │   ├── payment_refund.py            # Entity
            │   └── webhook_event.py             # Entity
            ├── value_objects/
            │   ├── __init__.py
            │   ├── money.py                     # Amount + Currency
            │   ├── transaction_reference.py     # Unique reference
            │   ├── provider_response.py         # Provider API response
            │   ├── payment_status.py            # Status enum
            │   └── card_details.py              # Card display info
            ├── aggregates/
            │   ├── __init__.py
            │   └── payment_aggregate.py         # Transaction + Refunds
            ├── repositories/
            │   ├── __init__.py
            │   ├── payment_repository.py        # Interface
            │   └── payment_repository_impl.py   # PostgreSQL implementation
            ├── services/
            │   ├── __init__.py
            │   ├── payment_processor.py         # Domain service
            │   └── refund_processor.py          # Domain service
            ├── events/
            │   ├── __init__.py
            │   ├── payment_created.py
            │   ├── payment_completed.py
            │   ├── payment_failed.py
            │   └── refund_processed.py
            └── exceptions/
                ├── __init__.py
                ├── payment_errors.py
                └── provider_errors.py
```

### 2.2 Core Domain Models

#### Aggregate Root: PaymentTransaction
```python
# ddd_refactored/domain/payment_processing/entities/payment_transaction.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from ..value_objects import Money, TransactionReference, PaymentStatus, ProviderResponse
from ..events import PaymentCreated, PaymentCompleted, PaymentFailed
from ..exceptions import InvalidTransactionStateError


@dataclass
class PaymentTransaction:
    """
    Aggregate Root for payment transactions.

    Invariants:
    - Transaction reference must be unique
    - Amount must be positive
    - Cannot refund more than transaction amount
    - Cannot complete a failed transaction
    """

    # Identity
    id: UUID = field(default_factory=uuid4)
    transaction_reference: TransactionReference = field(default_factory=TransactionReference.generate)

    # Relationships
    store_id: UUID
    provider_id: UUID
    store_provider_id: UUID
    order_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    payment_method_id: Optional[UUID] = None

    # Transaction details
    transaction_type: str  # 'charge', 'authorize', 'capture', 'void'
    amount: Money
    status: PaymentStatus = PaymentStatus.PENDING

    # Provider details
    provider_transaction_id: Optional[str] = None
    provider_response: Optional[ProviderResponse] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Security
    idempotency_key: Optional[str] = None
    ip_address: Optional[str] = None

    # Metadata
    metadata: dict = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Domain events
    _domain_events: List = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate invariants after initialization."""
        if self.amount.amount <= 0:
            raise ValueError("Transaction amount must be positive")

        if self.transaction_type not in ['charge', 'authorize', 'capture', 'void']:
            raise ValueError(f"Invalid transaction type: {self.transaction_type}")

        # Raise domain event
        self._domain_events.append(
            PaymentCreated(
                transaction_id=self.id,
                amount=self.amount,
                store_id=self.store_id,
                created_at=self.created_at
            )
        )

    def complete(self, provider_transaction_id: str, provider_response: ProviderResponse) -> None:
        """
        Mark transaction as completed.

        Business rules:
        - Can only complete pending/processing transactions
        - Provider transaction ID is required
        """
        if self.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise InvalidTransactionStateError(
                f"Cannot complete transaction in {self.status} status"
            )

        self.status = PaymentStatus.COMPLETED
        self.provider_transaction_id = provider_transaction_id
        self.provider_response = provider_response
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        self._domain_events.append(
            PaymentCompleted(
                transaction_id=self.id,
                provider_transaction_id=provider_transaction_id,
                completed_at=self.completed_at
            )
        )

    def fail(self, error_code: str, error_message: str) -> None:
        """Mark transaction as failed."""
        if self.status == PaymentStatus.COMPLETED:
            raise InvalidTransactionStateError("Cannot fail a completed transaction")

        self.status = PaymentStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

        self._domain_events.append(
            PaymentFailed(
                transaction_id=self.id,
                error_code=error_code,
                error_message=error_message,
                failed_at=self.updated_at
            )
        )

    def refund(self, amount: Money, reason: str, created_by: UUID) -> 'PaymentRefund':
        """
        Create a refund for this transaction.

        Business rules:
        - Can only refund completed transactions
        - Refund amount cannot exceed transaction amount
        """
        if self.status != PaymentStatus.COMPLETED:
            raise InvalidTransactionStateError("Can only refund completed transactions")

        if amount.amount > self.amount.amount:
            raise ValueError("Refund amount cannot exceed transaction amount")

        from .payment_refund import PaymentRefund
        return PaymentRefund(
            transaction_id=self.id,
            amount=amount,
            reason=reason,
            created_by=created_by
        )

    @property
    def domain_events(self) -> List:
        """Get domain events for this aggregate."""
        return self._domain_events.copy()

    def clear_events(self) -> None:
        """Clear domain events after publishing."""
        self._domain_events.clear()
```

#### Value Object: Money
```python
# ddd_refactored/domain/payment_processing/value_objects/money.py

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """
    Value object representing monetary amount.

    Invariants:
    - Amount must have exactly 2 decimal places
    - Currency must be valid ISO code
    """

    amount: Decimal
    currency: str = 'CAD'

    def __post_init__(self):
        # Ensure 2 decimal places
        object.__setattr__(self, 'amount', Decimal(self.amount).quantize(Decimal('0.01')))

        # Validate currency
        valid_currencies = ['CAD', 'USD']
        if self.currency not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}")

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    @classmethod
    def from_cents(cls, cents: int, currency: str = 'CAD') -> 'Money':
        """Create Money from cents (to avoid floating point issues)."""
        return cls(amount=Decimal(cents) / 100, currency=currency)

    @property
    def cents(self) -> int:
        """Get amount in cents."""
        return int(self.amount * 100)
```

#### Value Object: PaymentStatus
```python
# ddd_refactored/domain/payment_processing/value_objects/payment_status.py

from enum import Enum


class PaymentStatus(str, Enum):
    """Payment transaction status."""

    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    VOIDED = 'voided'

    def is_final(self) -> bool:
        """Check if status is final (cannot transition)."""
        return self in [self.COMPLETED, self.FAILED, self.REFUNDED, self.VOIDED]

    def can_refund(self) -> bool:
        """Check if transaction in this status can be refunded."""
        return self == self.COMPLETED

    def can_void(self) -> bool:
        """Check if transaction in this status can be voided."""
        return self in [self.PENDING, self.PROCESSING]
```

### 2.3 Repository Pattern

#### Repository Interface
```python
# ddd_refactored/domain/payment_processing/repositories/payment_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities import PaymentTransaction
from ..value_objects import TransactionReference


class PaymentRepository(ABC):
    """Repository interface for payment transactions."""

    @abstractmethod
    async def save(self, transaction: PaymentTransaction) -> None:
        """Save a payment transaction."""
        pass

    @abstractmethod
    async def find_by_id(self, transaction_id: UUID) -> Optional[PaymentTransaction]:
        """Find transaction by ID."""
        pass

    @abstractmethod
    async def find_by_reference(self, reference: TransactionReference) -> Optional[PaymentTransaction]:
        """Find transaction by reference."""
        pass

    @abstractmethod
    async def find_by_order(self, order_id: UUID) -> List[PaymentTransaction]:
        """Find all transactions for an order."""
        pass

    @abstractmethod
    async def find_by_store(self, store_id: UUID, limit: int = 100) -> List[PaymentTransaction]:
        """Find transactions for a store."""
        pass

    @abstractmethod
    async def find_by_idempotency_key(self, key: str) -> Optional[PaymentTransaction]:
        """Find transaction by idempotency key."""
        pass
```

---

## Phase 3: Provider Integration Layer

### 3.1 Provider Factory Pattern

**Keep existing files with modifications:**
- ✅ `services/payment/base.py` - Base provider interface
- ✅ `services/payment/clover_provider.py` - Clover implementation
- ✅ `services/payment/moneris_provider.py` - Moneris implementation
- ✅ `services/payment/interac_provider.py` - Interac implementation
- ✅ `services/payment/provider_factory.py` - Provider factory

**Changes Required:**
1. Update all providers to use `store_id` instead of `tenant_id`
2. Remove fee calculation logic from providers
3. Update credential loading to use `store_payment_providers` table
4. Simplify response objects (remove fee fields)

### 3.2 Provider Base Interface Updates

```python
# services/payment/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..ddd_refactored.domain.payment_processing.value_objects import Money


@dataclass
class PaymentRequest:
    """Store-level payment request."""
    store_id: UUID
    store_provider_id: UUID
    amount: Money
    payment_method_token: str
    order_id: Optional[UUID] = None
    idempotency_key: Optional[str] = None
    metadata: dict = None


@dataclass
class PaymentResponse:
    """Simplified payment response (no fees)."""
    success: bool
    transaction_id: str  # Provider's transaction ID
    status: str
    amount: Money
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: dict = None


class BasePaymentProvider(ABC):
    """Base payment provider interface."""

    @abstractmethod
    async def initialize(self, store_provider_id: UUID) -> None:
        """
        Initialize provider with store-specific credentials.

        Loads credentials from store_payment_providers table.
        """
        pass

    @abstractmethod
    async def charge(self, request: PaymentRequest) -> PaymentResponse:
        """Process a charge."""
        pass

    @abstractmethod
    async def refund(self, transaction_id: str, amount: Money, reason: str) -> PaymentResponse:
        """Process a refund."""
        pass

    @abstractmethod
    async def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Verify webhook signature."""
        pass
```

---

## Phase 4: API Layer (V2 Only)

### 4.1 V2 Endpoints Structure

```
Backend/api/v2/payments/
├── __init__.py
├── payment_endpoints.py          # Core transaction endpoints
├── provider_endpoints.py         # Provider management (store-level)
├── refund_endpoints.py           # Refund processing
├── webhook_endpoints.py          # Webhook handlers
└── schemas.py                    # Pydantic request/response models
```

### 4.2 Core V2 Endpoints

```python
# api/v2/payments/payment_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from ...ddd_refactored.application.services.payment_service import PaymentService
from ...ddd_refactored.domain.payment_processing.value_objects import Money
from .schemas import (
    CreatePaymentRequest,
    PaymentResponse,
    PaymentListResponse
)
from ...auth import get_current_user, require_permission


router = APIRouter(prefix="/api/v2/payments", tags=["Payments V2"])


@router.post("/stores/{store_id}/transactions", response_model=PaymentResponse)
async def create_payment(
    store_id: UUID,
    request: CreatePaymentRequest,
    payment_service: PaymentService = Depends(),
    current_user = Depends(get_current_user)
):
    """
    Create a new payment transaction for a store.

    This endpoint:
    1. Validates store-level payment provider configuration
    2. Processes payment through configured provider (Clover/Moneris/Interac)
    3. Records transaction in database
    4. Returns transaction details
    """
    try:
        # Use application service to orchestrate payment
        transaction = await payment_service.process_payment(
            store_id=store_id,
            amount=Money(request.amount, request.currency),
            payment_method_id=request.payment_method_id,
            order_id=request.order_id,
            idempotency_key=request.idempotency_key,
            user_id=current_user.id
        )

        return PaymentResponse.from_entity(transaction)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment processing failed")


@router.get("/stores/{store_id}/transactions", response_model=PaymentListResponse)
async def list_store_payments(
    store_id: UUID,
    limit: int = 100,
    offset: int = 0,
    payment_service: PaymentService = Depends(),
    current_user = Depends(get_current_user)
):
    """List payment transactions for a store."""
    transactions = await payment_service.get_store_transactions(
        store_id=store_id,
        limit=limit,
        offset=offset
    )

    return PaymentListResponse(
        transactions=[PaymentResponse.from_entity(t) for t in transactions],
        total=len(transactions),
        limit=limit,
        offset=offset
    )


@router.get("/transactions/{transaction_id}", response_model=PaymentResponse)
async def get_payment(
    transaction_id: UUID,
    payment_service: PaymentService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get payment transaction details."""
    transaction = await payment_service.get_transaction(transaction_id)

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    return PaymentResponse.from_entity(transaction)
```

### 4.3 Provider Management Endpoints (Store-Level)

```python
# api/v2/payments/provider_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from .schemas import (
    StoreProviderConfigRequest,
    StoreProviderResponse,
    CloverOAuthRequest
)
from ...services.store_payment_service import StorePaymentService
from ...auth import get_current_user, require_permission


router = APIRouter(prefix="/api/v2/payments/stores", tags=["Payment Providers V2"])


@router.post("/{store_id}/providers/{provider_type}/configure", response_model=StoreProviderResponse)
async def configure_store_provider(
    store_id: UUID,
    provider_type: str,  # 'clover', 'moneris', 'interac'
    request: StoreProviderConfigRequest,
    service: StorePaymentService = Depends(),
    current_user = Depends(require_permission("manage_payments"))
):
    """
    Configure a payment provider for a specific store.

    Replaces tenant-level configuration with store-level.
    Each store can have its own Clover terminal, Moneris account, etc.
    """
    if provider_type not in ['clover', 'moneris', 'interac']:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider_type}")

    store_provider = await service.configure_provider(
        store_id=store_id,
        provider_type=provider_type,
        credentials=request.credentials,
        configuration=request.configuration,
        is_default=request.is_default
    )

    return StoreProviderResponse.from_entity(store_provider)


@router.get("/{store_id}/providers", response_model=List[StoreProviderResponse])
async def list_store_providers(
    store_id: UUID,
    service: StorePaymentService = Depends(),
    current_user = Depends(get_current_user)
):
    """List all payment providers configured for a store."""
    providers = await service.get_store_providers(store_id)
    return [StoreProviderResponse.from_entity(p) for p in providers]


@router.delete("/{store_id}/providers/{provider_id}")
async def remove_store_provider(
    store_id: UUID,
    provider_id: UUID,
    service: StorePaymentService = Depends(),
    current_user = Depends(require_permission("manage_payments"))
):
    """Remove a payment provider from a store."""
    await service.remove_provider(store_id, provider_id)
    return {"status": "success", "message": "Provider removed"}
```

---

## Phase 5: Remove V1 Files

### 5.1 Files to DELETE

**V1 API Endpoints (7 files):**
```bash
rm /Backend/api/payment_endpoints.py                 # 737 lines - V1 payment processing
rm /Backend/api/payment_session_endpoints.py         # 278 lines - V1 Clover sessions
rm /Backend/api/payment_provider_endpoints.py        # 722 lines - V1 tenant-level providers
rm /Backend/api/payment_settings_endpoints.py        # V1 payment settings
rm /Backend/api/user_payment_endpoints.py            # V1 user payment methods
rm /Backend/api/client_payment_endpoints.py          # V1 client payments
rm /Backend/api/store_payment_endpoints.py           # V1 store payments (will be replaced by V2)
```

**V1 Services (2 files):**
```bash
rm /Backend/services/payment_service.py              # V1 payment orchestrator
rm /Backend/services/payment_service_v2.py           # Duplicate/incomplete V2 (wrong location)
```

**Migration Scripts (3 files - no longer needed):**
```bash
rm /Backend/migrations/add_payment_methods_to_profiles.sql
rm /Backend/migrations/clean_null_payment_methods.sql
rm /Backend/migrations/create_user_payment_methods.sql
```

**Test Files:**
```bash
rm /Backend/test_payment_method_fix.py
rm /Backend/run_payment_migration.py
```

### 5.2 Files to KEEP & UPDATE

**Provider Integrations:**
- ✅ `/Backend/services/payment/base.py` - Update for store-level
- ✅ `/Backend/services/payment/clover_provider.py` - Update for store-level
- ✅ `/Backend/services/payment/moneris_provider.py` - Update for store-level
- ✅ `/Backend/services/payment/interac_provider.py` - Update for store-level
- ✅ `/Backend/services/payment/provider_factory.py` - Update for store-level

**DDD Domain (partial - needs completion):**
- ✅ `/Backend/ddd_refactored/domain/payment_processing/entities/payment_transaction.py` - Refactor
- ✅ `/Backend/ddd_refactored/domain/payment_processing/value_objects/payment_types.py` - Extend

**New DDD Files to CREATE:**
- ✨ `ddd_refactored/domain/payment_processing/value_objects/money.py`
- ✨ `ddd_refactored/domain/payment_processing/repositories/payment_repository.py`
- ✨ `ddd_refactored/application/services/payment_service.py`

---

## Phase 6: Implementation Roadmap

### Week 1: Database Migration
- ✅ Day 1-2: Create and test migration scripts (001-004)
- ✅ Day 3: Run migrations on development database
- ✅ Day 4: Verify schema and seed providers
- ✅ Day 5: Create rollback scripts and test

### Week 2: DDD Domain Layer
- ✅ Day 1-2: Implement value objects (Money, PaymentStatus, TransactionReference)
- ✅ Day 3-4: Implement entities (PaymentTransaction, PaymentRefund)
- ✅ Day 5: Implement repository interfaces

### Week 3: Repository & Service Layer
- ✅ Day 1-2: Implement PostgreSQL repository
- ✅ Day 3-4: Implement domain services (PaymentProcessor, RefundProcessor)
- ✅ Day 5: Implement application service

### Week 4: Provider Integration Updates
- ✅ Day 1: Update Clover provider for store-level
- ✅ Day 2: Update Moneris provider for store-level
- ✅ Day 3: Update Interac provider for store-level
- ✅ Day 4: Update provider factory
- ✅ Day 5: Integration testing

### Week 5: V2 API Implementation
- ✅ Day 1-2: Implement payment transaction endpoints
- ✅ Day 3: Implement refund endpoints
- ✅ Day 4: Implement webhook endpoints
- ✅ Day 5: Implement provider management endpoints

### Week 6: V1 Deprecation & Testing
- ✅ Day 1: Remove V1 endpoint files
- ✅ Day 2: Remove V1 service files
- ✅ Day 3: Update API server registration
- ✅ Day 4-5: End-to-end testing with all 3 providers

---

## Phase 7: Testing Strategy

### 7.1 Unit Tests
```python
# tests/domain/test_payment_transaction.py
# tests/domain/test_money.py
# tests/domain/test_payment_status.py
# tests/repositories/test_payment_repository.py
```

### 7.2 Integration Tests
```python
# tests/integration/test_clover_payments.py
# tests/integration/test_moneris_payments.py
# tests/integration/test_interac_payments.py
```

### 7.3 API Tests
```python
# tests/api/test_payment_endpoints_v2.py
# tests/api/test_provider_endpoints_v2.py
# tests/api/test_webhook_endpoints_v2.py
```

---

## Risk Mitigation

### Risks
1. **Database migration complexity** → Mitigated by empty tables (no data to migrate)
2. **Provider credential migration** → Mitigated by new store-level configuration
3. **Frontend breaking changes** → Need to update frontend to use V2 endpoints
4. **Testing with real providers** → Use sandbox mode for all providers

### Rollback Plan
```sql
-- Restore from backups
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Restore from _backup_* tables
-- Re-run old migrations
```

---

## Success Metrics

✅ **Database simplified**: 16 tables → 6 tables (62.5% reduction)
✅ **Column reduction**: payment_transactions 38 → 17 (55% reduction)
✅ **Code removal**: ~2000 lines of V1 code deleted
✅ **Architecture clarity**: Single DDD system instead of dual V1/V2
✅ **Store-level granularity**: Correct business logic alignment
✅ **Provider focus**: 3 fully implemented providers (not 5 partial)

---

## Next Steps

1. **Review this plan** with team
2. **Create feature branch**: `feature/payment-refactor-store-level-ddd`
3. **Start Phase 1**: Database migration scripts
4. **Daily standups**: Track progress against 6-week timeline
5. **Weekly demos**: Show working features to stakeholders

---

**Document Version:** 1.0
**Last Updated:** 2025-01-18
**Owner:** Development Team
**Approver:** Technical Lead
