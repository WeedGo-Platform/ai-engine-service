-- RAG Knowledge Base Schema
-- PostgreSQL + pgvector for hybrid vector search
-- Partitioned by tenant_id and store_id for multi-tenancy

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge Documents Table
-- Stores metadata about documents in the knowledge base
CREATE TABLE IF NOT EXISTS knowledge_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- 'ocs_product', 'faq', 'compliance', 'platform_docs', 'store_info'
    tenant_id UUID, -- NULL for global documents
    store_id UUID, -- NULL for tenant-wide or global documents
    source_table VARCHAR(100), -- Original table name (e.g., 'ocs_product_catalog')
    source_id VARCHAR(255), -- ID in source table
    access_level VARCHAR(20) NOT NULL DEFAULT 'public', -- 'public', 'customer', 'platform', 'internal'
    language VARCHAR(10) DEFAULT 'en',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    indexed_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for knowledge_documents
CREATE INDEX idx_knowledge_docs_type ON knowledge_documents(document_type);
CREATE INDEX idx_knowledge_docs_tenant ON knowledge_documents(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_knowledge_docs_store ON knowledge_documents(store_id) WHERE store_id IS NOT NULL;
CREATE INDEX idx_knowledge_docs_source ON knowledge_documents(source_table, source_id);
CREATE INDEX idx_knowledge_docs_access ON knowledge_documents(access_level);
CREATE INDEX idx_knowledge_docs_active ON knowledge_documents(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_knowledge_docs_metadata ON knowledge_documents USING GIN(metadata);

-- Knowledge Chunks Table
-- Stores chunked text with embeddings
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(document_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL, -- Order within document
    embedding vector(384), -- Embedding dimension for all-MiniLM-L6-v2 or paraphrase-multilingual-MiniLM-L12-v2
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    token_count INTEGER,
    
    UNIQUE(document_id, chunk_index)
);

-- Indexes for knowledge_chunks
CREATE INDEX idx_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX idx_knowledge_chunks_embedding ON knowledge_chunks USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100); -- IVF index for fast vector search

-- Full-text search index on content
CREATE INDEX idx_knowledge_chunks_content_fts ON knowledge_chunks USING GIN(to_tsvector('english', content));

-- Composite index for common queries
CREATE INDEX idx_knowledge_chunks_doc_idx ON knowledge_chunks(document_id, chunk_index);

-- Knowledge Sync Status Table
-- Tracks synchronization with source tables
CREATE TABLE IF NOT EXISTS knowledge_sync_status (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_table VARCHAR(100) NOT NULL,
    tenant_id UUID,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_count INTEGER DEFAULT 0,
    last_sync_status VARCHAR(20), -- 'success', 'failed', 'in_progress'
    error_message TEXT,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    sync_frequency_minutes INTEGER DEFAULT 60,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_table, tenant_id)
);

CREATE INDEX idx_knowledge_sync_table ON knowledge_sync_status(source_table);
CREATE INDEX idx_knowledge_sync_next ON knowledge_sync_status(next_sync_at) WHERE last_sync_status != 'in_progress';

-- Query Analytics Table
-- Track query patterns for optimization
CREATE TABLE IF NOT EXISTS rag_query_analytics (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64), -- MD5 hash for deduplication
    tenant_id UUID,
    store_id UUID,
    agent_id VARCHAR(50),
    results_count INTEGER,
    top_document_types VARCHAR(100)[],
    latency_ms NUMERIC(10, 2),
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rag_analytics_hash ON rag_query_analytics(query_hash);
CREATE INDEX idx_rag_analytics_tenant ON rag_query_analytics(tenant_id);
CREATE INDEX idx_rag_analytics_agent ON rag_query_analytics(agent_id);
CREATE INDEX idx_rag_analytics_created ON rag_query_analytics(created_at);

-- Helper function: Update document timestamp
CREATE OR REPLACE FUNCTION update_knowledge_document_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE knowledge_documents
    SET updated_at = NOW()
    WHERE document_id = NEW.document_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_knowledge_timestamp
AFTER INSERT OR UPDATE ON knowledge_chunks
FOR EACH ROW
EXECUTE FUNCTION update_knowledge_document_timestamp();

-- Helper function: Get tenant-filtered chunks
CREATE OR REPLACE FUNCTION get_relevant_chunks(
    query_embedding vector(384),
    p_tenant_id UUID DEFAULT NULL,
    p_store_id UUID DEFAULT NULL,
    p_document_types VARCHAR(50)[] DEFAULT NULL,
    p_access_level VARCHAR(20) DEFAULT 'public',
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity NUMERIC,
    document_type VARCHAR(50),
    title VARCHAR(500)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        d.document_type,
        d.title
    FROM knowledge_chunks c
    JOIN knowledge_documents d ON c.document_id = d.document_id
    WHERE d.is_active = TRUE
        AND (p_tenant_id IS NULL OR d.tenant_id = p_tenant_id OR d.tenant_id IS NULL)
        AND (p_store_id IS NULL OR d.store_id = p_store_id OR d.store_id IS NULL)
        AND (p_document_types IS NULL OR d.document_type = ANY(p_document_types))
        AND d.access_level <= p_access_level
    ORDER BY c.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE knowledge_documents IS 'Master table for all knowledge base documents with multi-tenant support';
COMMENT ON TABLE knowledge_chunks IS 'Chunked text with embeddings for vector search';
COMMENT ON TABLE knowledge_sync_status IS 'Tracks synchronization status with source tables like ocs_product_catalog';
COMMENT ON COLUMN knowledge_documents.access_level IS 'public=all, customer=customer-facing agents, platform=sales agents, internal=admin only';
COMMENT ON COLUMN knowledge_chunks.embedding IS 'Vector embedding (384-dim for multilingual-MiniLM-L12-v2)';
