-- AGI System Missing Tables Migration
-- Created: 2025-09-27
-- Purpose: Add missing tables identified during implementation audit

-- 1. Document Embeddings Table (Required for RAG system)
CREATE TABLE IF NOT EXISTS agi.document_embeddings (
    chunk_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    embedding VECTOR(384), -- Using pgvector for efficient similarity search
    embedding_json JSONB, -- Fallback for non-vector databases
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES agi.knowledge_documents(id) ON DELETE CASCADE
);

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector
ON agi.document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for document lookup
CREATE INDEX IF NOT EXISTS idx_document_embeddings_document
ON agi.document_embeddings(document_id);

-- 2. Document Chunks Table (Required for RAG chunking)
CREATE TABLE IF NOT EXISTS agi.document_chunks (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    document_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    tokens INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES agi.knowledge_documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document
ON agi.document_chunks(document_id);

-- 3. Learning Feedback Table (Required for learning system)
CREATE TABLE IF NOT EXISTS agi.learning_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255),
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('explicit', 'implicit', 'correction', 'rating')),
    feedback_value FLOAT,
    feedback_text TEXT,
    context JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agi.sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_learning_feedback_session
ON agi.learning_feedback(session_id);

CREATE INDEX IF NOT EXISTS idx_learning_feedback_processed
ON agi.learning_feedback(processed) WHERE NOT processed;

-- 4. Agent Memories Table (Required for agent memory)
CREATE TABLE IF NOT EXISTS agi.agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('working', 'episodic', 'semantic', 'procedural')),
    content TEXT NOT NULL,
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    embedding VECTOR(384),
    embedding_json JSONB,
    context JSONB DEFAULT '{}',
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agi.agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_memories_agent
ON agi.agent_memories(agent_id, memory_type);

CREATE INDEX IF NOT EXISTS idx_agent_memories_importance
ON agi.agent_memories(importance DESC);

CREATE INDEX IF NOT EXISTS idx_agent_memories_embedding
ON agi.agent_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100)
WHERE embedding IS NOT NULL;

-- 5. Security Audit Log Table (Required for security auditing)
CREATE TABLE IF NOT EXISTS agi.security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    resource_id VARCHAR(255),
    result VARCHAR(50) CHECK (result IN ('success', 'failure', 'denied', 'error')),
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    response_code INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES agi.sessions(id) ON DELETE SET NULL
);

-- Optimized indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp
ON agi.security_audit_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_user
ON agi.security_audit_log(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_session
ON agi.security_audit_log(session_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_result
ON agi.security_audit_log(result) WHERE result != 'success';

-- 6. Fix metrics table - Add missing session_id column
ALTER TABLE agi.metrics
ADD COLUMN IF NOT EXISTS session_id VARCHAR(255);

-- Add foreign key constraint
ALTER TABLE agi.metrics
ADD CONSTRAINT fk_metrics_session
FOREIGN KEY (session_id)
REFERENCES agi.sessions(id)
ON DELETE CASCADE;

-- Add index for session-based queries
CREATE INDEX IF NOT EXISTS idx_metrics_session
ON agi.metrics(session_id, timestamp DESC);

-- 7. API Keys Table (Required for API authentication)
CREATE TABLE IF NOT EXISTS agi.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    tenant_id VARCHAR(255),
    permissions JSONB DEFAULT '[]',
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash
ON agi.api_keys(key_hash) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_api_keys_user
ON agi.api_keys(user_id);

-- 8. Users Table (Required for authentication)
CREATE TABLE IF NOT EXISTS agi.users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    roles JSONB DEFAULT '["user"]',
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username
ON agi.users(username) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_users_email
ON agi.users(email) WHERE email IS NOT NULL;

-- Add update trigger for updated_at columns
CREATE OR REPLACE FUNCTION agi.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_document_embeddings_updated_at BEFORE UPDATE
ON agi.document_embeddings FOR EACH ROW EXECUTE FUNCTION agi.update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
ON agi.users FOR EACH ROW EXECUTE FUNCTION agi.update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agi TO weedgo;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agi TO weedgo;