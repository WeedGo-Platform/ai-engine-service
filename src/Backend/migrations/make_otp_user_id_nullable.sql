-- Migration: Make user_id nullable in otp_codes table
-- This allows OTP codes to be created during signup before user exists
-- Date: 2025-10-29

BEGIN;

-- Drop the foreign key constraint
ALTER TABLE otp_codes DROP CONSTRAINT IF EXISTS otp_codes_user_id_fkey;

-- Make user_id column nullable
ALTER TABLE otp_codes ALTER COLUMN user_id DROP NOT NULL;

-- Recreate the foreign key constraint with ON DELETE SET NULL
-- This ensures data integrity while allowing null values
ALTER TABLE otp_codes 
ADD CONSTRAINT otp_codes_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES users(id) 
ON DELETE SET NULL;

-- Add index for performance on non-null user_id lookups
CREATE INDEX IF NOT EXISTS idx_otp_codes_user_id ON otp_codes(user_id) WHERE user_id IS NOT NULL;

COMMIT;
