-- Performance indexes for AI Engine context persistence
-- Run this script to optimize query performance for context retrieval

-- Indexes for ai_conversations table
CREATE INDEX IF NOT EXISTS idx_ai_conversations_session_id 
    ON ai_conversations(session_id);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_customer_id 
    ON ai_conversations(customer_id);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_created_at 
    ON ai_conversations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_session_customer 
    ON ai_conversations(session_id, customer_id);

-- Indexes for chat_interactions table
CREATE INDEX IF NOT EXISTS idx_chat_interactions_session_id 
    ON chat_interactions(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_interactions_customer_id 
    ON chat_interactions(customer_id);

CREATE INDEX IF NOT EXISTS idx_chat_interactions_created_at 
    ON chat_interactions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_interactions_session_customer 
    ON chat_interactions(session_id, customer_id);

CREATE INDEX IF NOT EXISTS idx_chat_interactions_intent 
    ON chat_interactions(intent);

-- Indexes for customer_profiles table
CREATE INDEX IF NOT EXISTS idx_customer_profiles_last_interaction 
    ON customer_profiles(last_interaction DESC);

-- Indexes for product_recommendations table
CREATE INDEX IF NOT EXISTS idx_product_recommendations_customer_id 
    ON product_recommendations(customer_id);

CREATE INDEX IF NOT EXISTS idx_product_recommendations_created_at 
    ON product_recommendations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_product_recommendations_customer_score 
    ON product_recommendations(customer_id, score DESC);

-- GIN indexes for JSONB columns (for fast JSON queries)
CREATE INDEX IF NOT EXISTS idx_ai_conversations_messages_gin 
    ON ai_conversations USING gin(messages);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_context_gin 
    ON ai_conversations USING gin(context);

CREATE INDEX IF NOT EXISTS idx_chat_interactions_metadata_gin 
    ON chat_interactions USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_customer_profiles_preferences_gin 
    ON customer_profiles USING gin(preferences);

CREATE INDEX IF NOT EXISTS idx_customer_profiles_purchase_history_gin 
    ON customer_profiles USING gin(purchase_history);

-- Partial indexes for active sessions (sessions updated in last 24 hours)
CREATE INDEX IF NOT EXISTS idx_ai_conversations_active 
    ON ai_conversations(session_id) 
    WHERE updated_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours');

-- Index for cleanup operations
CREATE INDEX IF NOT EXISTS idx_ai_conversations_cleanup 
    ON ai_conversations(updated_at) 
    WHERE updated_at < (CURRENT_TIMESTAMP - INTERVAL '7 days');

-- Analyze tables to update statistics
ANALYZE ai_conversations;
ANALYZE chat_interactions;
ANALYZE customer_profiles;
ANALYZE product_recommendations;