-- AGI System Fixed Missing Tables Migration
-- Fixed foreign key data type mismatches

-- 1. Document Embeddings Table
CREATE TABLE IF NOT EXISTS agi.document_embeddings (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    embedding_json JSONB NOT NULL,  -- Store as JSONB since pgvector not available
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES agi.knowledge_documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_document
ON agi.document_embeddings(document_id);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_json
ON agi.document_embeddings USING gin(embedding_json);

-- 2. Document Chunks Table
CREATE TABLE IF NOT EXISTS agi.document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
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

-- 3. Learning Feedback Table
CREATE TABLE IF NOT EXISTS agi.learning_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
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

-- 4. Agent Memories Table
CREATE TABLE IF NOT EXISTS agi.agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('working', 'episodic', 'semantic', 'procedural')),
    content TEXT NOT NULL,
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
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

-- 5. Security Audit Log Table
CREATE TABLE IF NOT EXISTS agi.security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    session_id UUID,
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

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp
ON agi.security_audit_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_user
ON agi.security_audit_log(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_session
ON agi.security_audit_log(session_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_result
ON agi.security_audit_log(result) WHERE result != 'success';