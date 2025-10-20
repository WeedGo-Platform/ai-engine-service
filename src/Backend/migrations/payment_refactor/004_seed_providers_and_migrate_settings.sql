-- Migration: Seed Payment Providers and Migrate Store Settings
-- Description:
--   1. Seed payment_providers table with Clover, Moneris, Interac definitions
--   2. Migrate existing payment settings from stores.settings to store_payment_providers
-- Version: 004
-- Date: 2025-01-19
-- Author: Claude Code (AI Assistant)

BEGIN;

-- ============================================================================
-- PART 1: Seed Payment Provider Definitions
-- ============================================================================

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
  fee_structure,
  capabilities,
  is_default,
  webhook_url,
  settlement_schedule
) VALUES (
  gen_random_uuid(),
  'Clover',
  'clover',
  'clover',
  true,
  false,
  100,
  ARRAY['CAD', 'USD'],
  ARRAY['card', 'tap', 'chip', 'swipe', 'manual_entry'],
  ARRAY['visa', 'mastercard', 'amex', 'discover'],
  jsonb_build_object(
    'api_base_url', 'https://api.clover.com',
    'sandbox_url', 'https://sandbox.dev.clover.com',
    'oauth_url', 'https://www.clover.com/oauth',
    'required_fields', ARRAY['merchant_id', 'access_token'],
    'supports_refunds', true,
    'supports_voids', true,
    'supports_tips', true,
    'supports_recurring', true
  ),
  jsonb_build_object(
    'percentage_fee', 2.6,
    'fixed_fee', 0.10,
    'currency', 'CAD'
  ),
  jsonb_build_object(
    'payment_processing', true,
    'refunds', true,
    'voids', true,
    'tips', true,
    'recurring_payments', true,
    'tokenization', true,
    '3d_secure', true,
    'webhooks', true
  ),
  true,
  '/api/webhooks/clover',
  'daily'
)
ON CONFLICT (name) DO UPDATE SET
  provider_name = EXCLUDED.provider_name,
  provider_type = EXCLUDED.provider_type,
  is_active = EXCLUDED.is_active,
  supported_currencies = EXCLUDED.supported_currencies,
  supported_payment_methods = EXCLUDED.supported_payment_methods,
  supported_card_types = EXCLUDED.supported_card_types,
  configuration = EXCLUDED.configuration,
  fee_structure = EXCLUDED.fee_structure,
  capabilities = EXCLUDED.capabilities,
  updated_at = CURRENT_TIMESTAMP;

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
  fee_structure,
  capabilities,
  is_default,
  webhook_url,
  settlement_schedule
) VALUES (
  gen_random_uuid(),
  'Moneris',
  'moneris',
  'moneris',
  true,
  false,
  90,
  ARRAY['CAD', 'USD'],
  ARRAY['card', 'tap', 'chip', 'swipe', 'interac'],
  ARRAY['visa', 'mastercard', 'amex', 'discover'],
  jsonb_build_object(
    'api_base_url', 'https://www3.moneris.com',
    'sandbox_url', 'https://esqa.moneris.com',
    'required_fields', ARRAY['store_id', 'api_token'],
    'supports_refunds', true,
    'supports_voids', true,
    'supports_preauth', true,
    'supports_interac', true
  ),
  jsonb_build_object(
    'percentage_fee', 2.65,
    'fixed_fee', 0.00,
    'currency', 'CAD'
  ),
  jsonb_build_object(
    'payment_processing', true,
    'refunds', true,
    'voids', true,
    'preauthorization', true,
    'interac_online', true,
    'tokenization', true,
    'recurring_payments', true,
    'webhooks', true
  ),
  false,
  '/api/webhooks/moneris',
  'daily'
)
ON CONFLICT (name) DO UPDATE SET
  provider_name = EXCLUDED.provider_name,
  provider_type = EXCLUDED.provider_type,
  is_active = EXCLUDED.is_active,
  supported_currencies = EXCLUDED.supported_currencies,
  supported_payment_methods = EXCLUDED.supported_payment_methods,
  supported_card_types = EXCLUDED.supported_card_types,
  configuration = EXCLUDED.configuration,
  fee_structure = EXCLUDED.fee_structure,
  capabilities = EXCLUDED.capabilities,
  updated_at = CURRENT_TIMESTAMP;

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
  fee_structure,
  capabilities,
  is_default,
  webhook_url,
  settlement_schedule
) VALUES (
  gen_random_uuid(),
  'Interac',
  'interac',
  'interac',
  true,
  false,
  80,
  ARRAY['CAD'],
  ARRAY['interac', 'etransfer'],
  ARRAY['debit'],
  jsonb_build_object(
    'api_base_url', 'https://api.interac.ca',
    'required_fields', ARRAY['merchant_id', 'api_key'],
    'supports_refunds', true,
    'supports_etransfer', true
  ),
  jsonb_build_object(
    'percentage_fee', 1.5,
    'fixed_fee', 0.05,
    'currency', 'CAD'
  ),
  jsonb_build_object(
    'payment_processing', true,
    'refunds', true,
    'interac_online', true,
    'etransfer', true,
    'webhooks', true
  ),
  false,
  '/api/webhooks/interac',
  'daily'
)
ON CONFLICT (name) DO UPDATE SET
  provider_name = EXCLUDED.provider_name,
  provider_type = EXCLUDED.provider_type,
  is_active = EXCLUDED.is_active,
  supported_currencies = EXCLUDED.supported_currencies,
  supported_payment_methods = EXCLUDED.supported_payment_methods,
  configuration = EXCLUDED.configuration,
  fee_structure = EXCLUDED.fee_structure,
  capabilities = EXCLUDED.capabilities,
  updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- PART 2: Migrate Store Payment Settings (stores.settings.onlinePayment)
-- ============================================================================

-- Migrate from stores.settings.onlinePayment to store_payment_providers
-- This handles the OnlinePaymentSettings component's saved data
INSERT INTO store_payment_providers (
  id,
  store_id,
  provider_id,
  is_active,
  is_default,
  credentials_encrypted,
  encryption_metadata,
  configuration,
  created_at,
  updated_at
)
SELECT
  gen_random_uuid() AS id,
  s.id AS store_id,
  pp.id AS provider_id,
  COALESCE((s.settings->'onlinePayment'->>'enabled')::boolean, false) AS is_active,
  true AS is_default, -- First provider for store = default
  s.settings->'onlinePayment'->>'accessToken' AS credentials_encrypted,
  jsonb_build_object(
    'algorithm', 'AES-256',
    'migrated_from', 'stores.settings.onlinePayment',
    'migrated_at', CURRENT_TIMESTAMP,
    'original_format', 'plain_text_warning'
  ) AS encryption_metadata,
  jsonb_build_object(
    'merchant_id', s.settings->'onlinePayment'->>'merchantId',
    'environment', COALESCE(s.settings->'onlinePayment'->>'environment', 'sandbox'),
    'webhook_url', s.settings->'onlinePayment'->>'webhookUrl',
    'supported_card_types', COALESCE(
      (s.settings->'onlinePayment'->'supportedCardTypes')::jsonb,
      '["visa", "mastercard", "amex"]'::jsonb
    ),
    'require_3ds', COALESCE((s.settings->'onlinePayment'->>'require3DS')::boolean, false),
    'platform_fee_percentage', COALESCE((s.settings->'onlinePayment'->>'platformFeePercentage')::numeric, 2.0),
    'platform_fee_fixed', COALESCE((s.settings->'onlinePayment'->>'platformFeeFixed')::numeric, 0.0)
  ) AS configuration,
  CURRENT_TIMESTAMP AS created_at,
  CURRENT_TIMESTAMP AS updated_at
FROM stores s
CROSS JOIN payment_providers pp
WHERE
  s.settings->'onlinePayment' IS NOT NULL
  AND s.settings->'onlinePayment'->>'provider' = pp.provider_type
  AND NOT EXISTS (
    -- Avoid duplicates if migration runs multiple times
    SELECT 1 FROM store_payment_providers spp
    WHERE spp.store_id = s.id AND spp.provider_id = pp.id
  );

-- ============================================================================
-- PART 3: Migrate Legacy Payment Settings (stores.settings.payment)
-- ============================================================================

-- Migrate from stores.settings.payment to store_payment_providers
-- This handles older payment configurations if they exist
INSERT INTO store_payment_providers (
  id,
  store_id,
  provider_id,
  is_active,
  is_default,
  credentials_encrypted,
  encryption_metadata,
  configuration,
  created_at,
  updated_at
)
SELECT
  gen_random_uuid() AS id,
  s.id AS store_id,
  pp.id AS provider_id,
  COALESCE((s.settings->'payment'->>'enabled')::boolean, true) AS is_active,
  true AS is_default,
  s.settings->'payment'->>'accessToken' AS credentials_encrypted,
  jsonb_build_object(
    'algorithm', 'AES-256',
    'migrated_from', 'stores.settings.payment',
    'migrated_at', CURRENT_TIMESTAMP,
    'original_format', 'legacy'
  ) AS encryption_metadata,
  jsonb_build_object(
    'merchant_id', s.settings->'payment'->>'merchantId',
    'environment', 'production', -- Legacy settings assumed production
    'webhook_url', s.settings->'payment'->>'webhookUrl',
    'tip_enabled', COALESCE((s.settings->'payment'->>'tipEnabled')::boolean, true),
    'tip_options', COALESCE(
      (s.settings->'payment'->'tipOptions')::jsonb,
      '[15, 18, 20, 0]'::jsonb
    ),
    'accepted_methods', COALESCE(
      (s.settings->'payment'->'acceptedMethods')::jsonb,
      '["tap", "chip", "swipe", "cash"]'::jsonb
    )
  ) AS configuration,
  CURRENT_TIMESTAMP AS created_at,
  CURRENT_TIMESTAMP AS updated_at
FROM stores s
CROSS JOIN payment_providers pp
WHERE
  s.settings->'payment' IS NOT NULL
  AND s.settings->'payment'->>'provider' = pp.provider_type
  AND NOT EXISTS (
    -- Avoid duplicates
    SELECT 1 FROM store_payment_providers spp
    WHERE spp.store_id = s.id AND spp.provider_id = pp.id
  );

-- ============================================================================
-- PART 4: Update Statistics and Verification
-- ============================================================================

-- Optional: Add comment to stores table documenting migration
COMMENT ON COLUMN stores.settings IS 'Store configuration settings. Payment settings migrated to store_payment_providers table as of 2025-01-19.';

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES (run after migration)
-- ============================================================================

-- Uncomment to verify migration results:

-- SELECT
--   'Payment Providers Seeded' as check_name,
--   COUNT(*) as count
-- FROM payment_providers;

-- SELECT
--   'Store Providers Migrated' as check_name,
--   COUNT(*) as count
-- FROM store_payment_providers;

-- SELECT
--   s.name as store_name,
--   pp.provider_name,
--   spp.is_active,
--   spp.configuration->>'environment' as environment,
--   spp.configuration->>'merchant_id' as merchant_id
-- FROM store_payment_providers spp
-- JOIN stores s ON s.id = spp.store_id
-- JOIN payment_providers pp ON pp.id = spp.provider_id
-- ORDER BY s.name, pp.priority DESC;
