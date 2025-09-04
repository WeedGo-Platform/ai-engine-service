-- Add conversation context columns to track product references
-- Run this migration to enable full conversation context tracking

-- Add columns to conversation_messages table if they don't exist
ALTER TABLE conversation_messages 
ADD COLUMN IF NOT EXISTS products_shown JSONB,
ADD COLUMN IF NOT EXISTS intent_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS referenced_products JSONB;

-- Create index for faster session lookups
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session 
ON conversation_messages(session_id, created_at DESC);

-- Create a conversation context table for session state
CREATE TABLE IF NOT EXISTS conversation_context (
    session_id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255),
    last_products_shown JSONB,
    last_intent VARCHAR(50),
    user_preferences JSONB,
    last_search_criteria JSONB,
    current_cart JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for customer lookups
CREATE INDEX IF NOT EXISTS idx_conversation_context_customer 
ON conversation_context(customer_id);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_context_updated_at 
BEFORE UPDATE ON conversation_context
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();