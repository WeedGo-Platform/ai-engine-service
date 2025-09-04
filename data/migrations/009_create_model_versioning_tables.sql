-- Create model versioning tables for AI model persistence and management

-- Model versions table - tracks all model versions and their metadata
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    version_id VARCHAR(255) UNIQUE NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    base_model VARCHAR(255) NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) DEFAULT 'llama', -- llama, mistral, etc.
    model_size VARCHAR(50), -- 7B, 13B, 70B, etc.
    quantization VARCHAR(20), -- Q4_K_M, Q5_K_S, Q8_0, etc.
    
    -- Training metadata
    training_method VARCHAR(50), -- full, lora, qlora
    adapter_config JSONB DEFAULT '{}',
    training_params JSONB DEFAULT '{}',
    datasets_used JSONB DEFAULT '[]',
    training_examples_count INTEGER DEFAULT 0,
    
    -- Performance metrics
    accuracy FLOAT,
    loss FLOAT,
    perplexity FLOAT,
    eval_metrics JSONB DEFAULT '{}',
    benchmark_scores JSONB DEFAULT '{}',
    
    -- File paths and storage
    model_path TEXT NOT NULL,
    adapter_path TEXT,
    checkpoint_path TEXT,
    file_size_mb FLOAT,
    
    -- Status and deployment
    status VARCHAR(50) DEFAULT 'training', -- training, ready, deployed, archived, failed
    is_active BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    deployment_env VARCHAR(50), -- dev, staging, production
    
    -- Metadata
    description TEXT,
    release_notes TEXT,
    tags JSONB DEFAULT '[]',
    created_by VARCHAR(100) DEFAULT 'system',
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training checkpoints table - tracks intermediate training states
CREATE TABLE IF NOT EXISTS training_checkpoints (
    id SERIAL PRIMARY KEY,
    checkpoint_id VARCHAR(255) UNIQUE NOT NULL,
    model_version_id INTEGER REFERENCES model_versions(id) ON DELETE CASCADE,
    session_id VARCHAR(255) REFERENCES training_sessions(session_id),
    
    epoch INTEGER NOT NULL,
    step INTEGER NOT NULL,
    total_steps INTEGER,
    
    -- Metrics at checkpoint
    train_loss FLOAT,
    eval_loss FLOAT,
    learning_rate FLOAT,
    gradient_norm FLOAT,
    
    -- File information
    checkpoint_path TEXT NOT NULL,
    file_size_mb FLOAT,
    
    -- Status
    is_best BOOLEAN DEFAULT FALSE,
    is_saved BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model evaluations table - tracks evaluation results
CREATE TABLE IF NOT EXISTS model_evaluations (
    id SERIAL PRIMARY KEY,
    evaluation_id VARCHAR(255) UNIQUE NOT NULL,
    model_version_id INTEGER REFERENCES model_versions(id) ON DELETE CASCADE,
    
    evaluation_type VARCHAR(50) NOT NULL, -- accuracy, benchmark, user_feedback, a_b_test
    dataset_used VARCHAR(255),
    test_examples_count INTEGER,
    
    -- Results
    metrics JSONB NOT NULL DEFAULT '{}',
    confusion_matrix JSONB,
    classification_report JSONB,
    
    -- Comparison
    baseline_version_id INTEGER REFERENCES model_versions(id),
    improvement_percentage FLOAT,
    
    -- User feedback
    user_ratings JSONB DEFAULT '[]',
    average_rating FLOAT,
    feedback_count INTEGER DEFAULT 0,
    
    notes TEXT,
    evaluator VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model deployments table - tracks deployment history
CREATE TABLE IF NOT EXISTS model_deployments (
    id SERIAL PRIMARY KEY,
    deployment_id VARCHAR(255) UNIQUE NOT NULL,
    model_version_id INTEGER REFERENCES model_versions(id) ON DELETE CASCADE,
    
    environment VARCHAR(50) NOT NULL, -- dev, staging, production
    deployment_type VARCHAR(50) DEFAULT 'replace', -- replace, canary, shadow, a_b_test
    
    -- A/B testing configuration
    traffic_percentage FLOAT DEFAULT 100,
    target_segments JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, deploying, active, inactive, failed
    deployed_at TIMESTAMP,
    undeployed_at TIMESTAMP,
    
    -- Performance tracking
    request_count INTEGER DEFAULT 0,
    average_latency_ms FLOAT,
    error_rate FLOAT,
    
    -- Rollback information
    previous_version_id INTEGER REFERENCES model_versions(id),
    rollback_reason TEXT,
    rolled_back_at TIMESTAMP,
    
    deployed_by VARCHAR(100),
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model lineage table - tracks relationships between models
CREATE TABLE IF NOT EXISTS model_lineage (
    id SERIAL PRIMARY KEY,
    parent_version_id INTEGER REFERENCES model_versions(id) ON DELETE CASCADE,
    child_version_id INTEGER REFERENCES model_versions(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- fine_tuned, merged, pruned, quantized
    
    transformation_details JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(parent_version_id, child_version_id)
);

-- Base models registry - tracks available base models
CREATE TABLE IF NOT EXISTS base_models (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(255) UNIQUE NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    model_family VARCHAR(100), -- llama2, llama3, mistral, etc.
    model_size VARCHAR(50), -- 7B, 13B, 70B
    
    -- Source information
    source VARCHAR(100), -- huggingface, local, custom
    source_url TEXT,
    license VARCHAR(100),
    
    -- File information
    file_path TEXT NOT NULL,
    file_format VARCHAR(20), -- gguf, safetensors, pytorch
    file_size_gb FLOAT,
    checksum VARCHAR(255),
    
    -- Capabilities
    capabilities JSONB DEFAULT '[]', -- text-generation, chat, instruction-following
    supported_languages JSONB DEFAULT '["en"]',
    context_length INTEGER DEFAULT 4096,
    
    -- Requirements
    min_gpu_memory_gb FLOAT,
    recommended_gpu_memory_gb FLOAT,
    supports_cpu BOOLEAN DEFAULT TRUE,
    
    -- Status
    is_available BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    download_status VARCHAR(50), -- downloaded, downloading, pending, failed
    
    -- Metadata
    description TEXT,
    release_date DATE,
    paper_url TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_model_versions_status ON model_versions(status);
CREATE INDEX IF NOT EXISTS idx_model_versions_active ON model_versions(is_active);
CREATE INDEX IF NOT EXISTS idx_model_versions_created ON model_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_versions_version ON model_versions(version_number);

CREATE INDEX IF NOT EXISTS idx_checkpoints_model ON training_checkpoints(model_version_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON training_checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_best ON training_checkpoints(is_best);

CREATE INDEX IF NOT EXISTS idx_evaluations_model ON model_evaluations(model_version_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_type ON model_evaluations(evaluation_type);

CREATE INDEX IF NOT EXISTS idx_deployments_model ON model_deployments(model_version_id);
CREATE INDEX IF NOT EXISTS idx_deployments_env ON model_deployments(environment);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON model_deployments(status);

CREATE INDEX IF NOT EXISTS idx_lineage_parent ON model_lineage(parent_version_id);
CREATE INDEX IF NOT EXISTS idx_lineage_child ON model_lineage(child_version_id);

CREATE INDEX IF NOT EXISTS idx_base_models_family ON base_models(model_family);
CREATE INDEX IF NOT EXISTS idx_base_models_available ON base_models(is_available);

-- Create update trigger for model_versions
CREATE OR REPLACE FUNCTION update_model_versions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER model_versions_updated_at_trigger
BEFORE UPDATE ON model_versions
FOR EACH ROW
EXECUTE FUNCTION update_model_versions_updated_at();

-- Insert default base model (Llama 3.2 3B for efficiency)
INSERT INTO base_models (
    model_id,
    model_name,
    model_family,
    model_size,
    source,
    source_url,
    license,
    file_path,
    file_format,
    file_size_gb,
    capabilities,
    context_length,
    min_gpu_memory_gb,
    recommended_gpu_memory_gb,
    supports_cpu,
    is_available,
    is_default,
    download_status,
    description
) VALUES (
    'llama-3.2-3b-instruct-q4',
    'Llama 3.2 3B Instruct Q4_K_M',
    'llama3',
    '3B',
    'huggingface',
    'https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF',
    'Meta Custom',
    '/models/base/llama-3.2-3b-instruct-q4_k_m.gguf',
    'gguf',
    2.0,
    '["text-generation", "chat", "instruction-following", "cannabis-knowledge"]',
    8192,
    4.0,
    6.0,
    true,
    false, -- Will be downloaded on first use
    true,
    'pending',
    'Efficient 3B parameter model optimized for cannabis dispensary assistance. Provides fast responses with good accuracy for product recommendations and customer queries.'
) ON CONFLICT (model_id) DO NOTHING;

-- Add comments to tables
COMMENT ON TABLE model_versions IS 'Tracks all AI model versions, their training parameters, and deployment status';
COMMENT ON TABLE training_checkpoints IS 'Stores intermediate training states for model recovery and analysis';
COMMENT ON TABLE model_evaluations IS 'Records evaluation results and performance metrics for model versions';
COMMENT ON TABLE model_deployments IS 'Tracks deployment history and A/B testing configurations';
COMMENT ON TABLE model_lineage IS 'Maintains parent-child relationships between model versions';
COMMENT ON TABLE base_models IS 'Registry of available base models for fine-tuning';