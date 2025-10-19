-- Migration: 004_seed_payment_providers.sql
-- Purpose: Seed the 3 payment providers (Clover, Moneris, Interac)
-- Date: 2025-01-18
-- Note: Creates sandbox configurations for testing

BEGIN;

-- ============================================================================
-- PROVIDER 1: Clover
-- Priority: 1 (highest)
-- Capabilities: Full card processing, tokenization, refunds, OAuth
-- ============================================================================

INSERT INTO payment_providers (
    id,
    provider_name,
    provider_type,
    name,
    is_active,
    is_sandbox,
    is_default,
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
    true, -- Sandbox mode for testing
    false,
    1, -- Highest priority
    ARRAY['CAD', 'USD'],
    ARRAY['card', 'contactless', 'chip', 'swipe'],
    ARRAY['visa', 'mastercard', 'amex', 'discover'],
    jsonb_build_object(
        'api_url', 'https://sandbox.dev.clover.com',
        'oauth_url', 'https://sandbox.dev.clover.com/oauth',
        'api_version', 'v3',
        'supports_oauth', true,
        'requires_merchant_id', true
    ),
    jsonb_build_object(
        'tokenization', true,
        'refunds', true,
        'partial_refunds', true,
        'void', true,
        'capture', true,
        'preauth', true,
        'recurring', false,
        'webhooks', true,
        'oauth', true
    ),
    '/api/v2/payments/webhooks/clover'
) ON CONFLICT (provider_name) DO UPDATE SET
    is_active = EXCLUDED.is_active,
    configuration = EXCLUDED.configuration,
    capabilities = EXCLUDED.capabilities,
    updated_at = CURRENT_TIMESTAMP;

RAISE NOTICE 'Seeded Clover provider (sandbox mode)';

-- ============================================================================
-- PROVIDER 2: Moneris
-- Priority: 2
-- Capabilities: Canadian payments, Interac debit, card processing
-- ============================================================================

INSERT INTO payment_providers (
    id,
    provider_name,
    provider_type,
    name,
    is_active,
    is_sandbox,
    is_default,
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
    true, -- Sandbox mode for testing
    false,
    2,
    ARRAY['CAD'], -- Canadian only
    ARRAY['card', 'interac_debit', 'chip', 'contactless'],
    ARRAY['visa', 'mastercard', 'amex'],
    jsonb_build_object(
        'api_url', 'https://esqa.moneris.com/gateway2/servlet/MpgRequest',
        'hosted_tokenization_url', 'https://esqa.moneris.com/HPPtoken/index.php',
        'api_version', '7',
        'country', 'CA',
        'requires_store_id', true,
        'requires_api_token', true
    ),
    jsonb_build_object(
        'tokenization', true,
        'refunds', true,
        'partial_refunds', true,
        'void', true,
        'capture', true,
        'preauth', true,
        'interac', true,
        'recurring', false,
        'webhooks', false
    ),
    '/api/v2/payments/webhooks/moneris'
) ON CONFLICT (provider_name) DO UPDATE SET
    is_active = EXCLUDED.is_active,
    configuration = EXCLUDED.configuration,
    capabilities = EXCLUDED.capabilities,
    updated_at = CURRENT_TIMESTAMP;

RAISE NOTICE 'Seeded Moneris provider (sandbox mode, Canadian)';

-- ============================================================================
-- PROVIDER 3: Interac
-- Priority: 3
-- Capabilities: e-Transfer, Interac debit (Canadian only)
-- ============================================================================

INSERT INTO payment_providers (
    id,
    provider_name,
    provider_type,
    name,
    is_active,
    is_sandbox,
    is_default,
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
    true, -- Sandbox mode for testing
    false,
    3,
    ARRAY['CAD'], -- Canadian only
    ARRAY['interac_etransfer', 'interac_debit'],
    ARRAY[], -- No card support (Interac is debit/e-Transfer only)
    jsonb_build_object(
        'api_url', 'https://gateway-sandbox.interac.ca',
        'etransfer_enabled', true,
        'api_version', '2',
        'country', 'CA',
        'requires_partner_id', true
    ),
    jsonb_build_object(
        'etransfer', true,
        'debit', true,
        'refunds', true,
        'partial_refunds', false,
        'void', false,
        'capture', false,
        'preauth', false,
        'recurring', false,
        'webhooks', true,
        'notifications', true
    ),
    '/api/v2/payments/webhooks/interac'
) ON CONFLICT (provider_name) DO UPDATE SET
    is_active = EXCLUDED.is_active,
    configuration = EXCLUDED.configuration,
    capabilities = EXCLUDED.capabilities,
    updated_at = CURRENT_TIMESTAMP;

RAISE NOTICE 'Seeded Interac provider (sandbox mode, Canadian)';

-- ============================================================================
-- LOG MIGRATION
-- ============================================================================

INSERT INTO migration_log (migration_name, status, started_at, completed_at)
VALUES ('004_seed_payment_providers', 'completed', NOW(), NOW());

COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show seeded providers
SELECT
    provider_type,
    provider_name,
    is_active,
    is_sandbox,
    priority,
    supported_currencies,
    array_length(supported_payment_methods, 1) as payment_methods_count,
    array_length(supported_card_types, 1) as card_types_count,
    webhook_url
FROM payment_providers
ORDER BY priority;

-- Success message
SELECT '
Migration 004_seed_payment_providers completed successfully!

Seeded 3 payment providers:
1. Clover (Priority 1) - Full card processing, OAuth, CAD/USD
2. Moneris (Priority 2) - Canadian payments, Interac debit, CAD only
3. Interac (Priority 3) - e-Transfer, Interac debit, CAD only

All providers configured in SANDBOX mode for testing.

Next steps:
- Configure store-specific credentials via store_payment_providers table
- Update provider integrations for store-level architecture
- Implement DDD domain models
' AS message;
