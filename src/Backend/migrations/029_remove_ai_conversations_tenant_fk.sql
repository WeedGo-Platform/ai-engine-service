-- Migration: Remove foreign key constraint from ai_conversations to tenants
-- Date: 2025-09-19
-- Description: Remove the dependency between ai_conversations and tenants table
--              to allow independent management of tenants without affecting AI conversations

-- Drop the foreign key constraint
ALTER TABLE ai_conversations
DROP CONSTRAINT IF EXISTS ai_conversations_tenant_id_fkey;

-- Note: We're keeping the tenant_id column for reference purposes
-- but removing the foreign key constraint to eliminate the dependency

-- Add a comment to document the change
COMMENT ON COLUMN ai_conversations.tenant_id IS
'Tenant ID reference (no FK constraint) - maintains historical association without enforcing referential integrity';