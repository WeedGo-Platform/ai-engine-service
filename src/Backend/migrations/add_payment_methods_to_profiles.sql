-- Add payment_methods JSONB column to profiles table
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS payment_methods JSONB DEFAULT '[]'::jsonb;

-- Add GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_profiles_payment_methods_gin ON profiles USING gin(payment_methods);

-- Drop the user_payment_methods table (rollback)
DROP TABLE IF EXISTS user_payment_methods CASCADE;

COMMENT ON COLUMN profiles.payment_methods IS 'Array of payment method objects: [{id, type, nickname, card_brand, last4, is_default, created_at}]';
