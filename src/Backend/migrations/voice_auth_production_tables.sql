-- Production Voice Authentication Database Schema Updates
-- Adds fields required for production voice biometric system

-- Add new columns to voice_profiles table
ALTER TABLE voice_profiles
ADD COLUMN IF NOT EXISTS quality_score FLOAT,
ADD COLUMN IF NOT EXISTS liveness_score FLOAT,
ADD COLUMN IF NOT EXISTS antispoofing_score FLOAT,
ADD COLUMN IF NOT EXISTS model_version VARCHAR(50),
ADD COLUMN IF NOT EXISTS embedding_encrypted BOOLEAN DEFAULT true;

-- Add new columns to voice_auth_logs table
ALTER TABLE voice_auth_logs
ADD COLUMN IF NOT EXISTS threshold_used FLOAT,
ADD COLUMN IF NOT EXISTS quality_score FLOAT,
ADD COLUMN IF NOT EXISTS liveness_score FLOAT,
ADD COLUMN IF NOT EXISTS antispoofing_score FLOAT,
ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Add new columns to users table for voice enrollment tracking
ALTER TABLE users
ADD COLUMN IF NOT EXISTS voice_enrolled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS voice_enrollment_date TIMESTAMP;

-- Create voice enrollment logs table
CREATE TABLE IF NOT EXISTS voice_enrollment_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    success BOOLEAN NOT NULL,
    age_info JSONB,
    quality_score FLOAT,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for voice enrollment logs
CREATE INDEX IF NOT EXISTS idx_enrollment_logs_user_id ON voice_enrollment_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_logs_timestamp ON voice_enrollment_logs(timestamp);

-- Update age_verification_logs table
ALTER TABLE age_verification_logs
ADD COLUMN IF NOT EXISTS confidence FLOAT,
ADD COLUMN IF NOT EXISTS quality_score FLOAT,
ADD COLUMN IF NOT EXISTS acoustic_features JSONB;

-- Create voice model configurations table
CREATE TABLE IF NOT EXISTS voice_model_configs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- speaker_verification, age_detection, antispoofing
    model_path TEXT NOT NULL,
    version VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default model configurations
INSERT INTO voice_model_configs (model_name, model_type, model_path, version, config, is_active)
VALUES
    ('ecapa-tdnn', 'speaker_verification', 'models/voice/biometric/speaker_verification/ecapa_tdnn.onnx', '1.0.0',
     '{"embedding_size": 192, "sample_rate": 16000, "quantized": true}', true),
    ('resnet34-se', 'speaker_verification', 'models/voice/biometric/speaker_verification/resnet34_se.onnx', '1.0.0',
     '{"embedding_size": 256, "sample_rate": 16000, "enabled": true}', true),
    ('wav2vec2-age', 'age_detection', 'models/voice/biometric/age_detection/wav2vec2_age.onnx', '1.0.0',
     '{"features": ["f0", "formants", "mfcc", "spectral_centroid", "jitter", "shimmer"]}', true),
    ('aasist', 'antispoofing', 'models/voice/biometric/antispoofing/aasist_l.onnx', '1.0.0',
     '{"threshold": 0.5}', true)
ON CONFLICT DO NOTHING;

-- Create voice authentication metrics table for analytics
CREATE TABLE IF NOT EXISTS voice_auth_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    total_authentications INTEGER DEFAULT 0,
    successful_authentications INTEGER DEFAULT 0,
    failed_authentications INTEGER DEFAULT 0,
    avg_processing_time_ms FLOAT,
    false_accept_rate FLOAT,
    false_reject_rate FLOAT,
    equal_error_rate FLOAT,
    unique_users INTEGER DEFAULT 0,
    age_verifications INTEGER DEFAULT 0,
    liveness_detections INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for metrics
CREATE INDEX IF NOT EXISTS idx_auth_metrics_date ON voice_auth_metrics(metric_date);

-- Create FAISS index metadata table
CREATE TABLE IF NOT EXISTS faiss_index_metadata (
    id SERIAL PRIMARY KEY,
    index_name VARCHAR(100) NOT NULL,
    index_type VARCHAR(50) NOT NULL,
    embedding_count INTEGER DEFAULT 0,
    embedding_dim INTEGER NOT NULL,
    last_rebuild TIMESTAMP,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create voice authentication sessions table
CREATE TABLE IF NOT EXISTS voice_auth_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) REFERENCES users(id),
    auth_type VARCHAR(50) NOT NULL, -- enrollment, verification, age_check
    status VARCHAR(50) NOT NULL, -- pending, processing, completed, failed
    attempts INTEGER DEFAULT 0,
    quality_scores JSONB,
    liveness_scores JSONB,
    metadata JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes for sessions
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON voice_auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_session_id ON voice_auth_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_status ON voice_auth_sessions(status);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_voice_model_configs_updated_at BEFORE UPDATE ON voice_model_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faiss_index_metadata_updated_at BEFORE UPDATE ON faiss_index_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for authentication statistics
CREATE OR REPLACE VIEW voice_auth_statistics AS
SELECT
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed,
    AVG(confidence_score) as avg_confidence,
    AVG(quality_score) as avg_quality,
    AVG(liveness_score) as avg_liveness,
    COUNT(DISTINCT user_id) as unique_users
FROM voice_auth_logs
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date DESC;

-- Create view for user voice profiles with enrollment status
CREATE OR REPLACE VIEW user_voice_profiles AS
SELECT
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.age_verified,
    u.voice_enrolled,
    u.voice_enrollment_date,
    vp.quality_score,
    vp.liveness_score,
    vp.created_at as profile_created,
    vp.updated_at as profile_updated,
    vp.age_verification,
    CASE
        WHEN vp.user_id IS NOT NULL THEN 'enrolled'
        ELSE 'not_enrolled'
    END as enrollment_status
FROM users u
LEFT JOIN voice_profiles vp ON u.id = vp.user_id
WHERE u.active = true;

-- Grant permissions (adjust based on your user roles)
-- GRANT SELECT ON voice_auth_statistics TO readonly_role;
-- GRANT SELECT ON user_voice_profiles TO readonly_role;
-- GRANT ALL ON voice_model_configs TO admin_role;

-- Add comments for documentation
COMMENT ON TABLE voice_model_configs IS 'Configuration for voice authentication ML models';
COMMENT ON TABLE voice_auth_metrics IS 'Daily aggregated metrics for voice authentication performance';
COMMENT ON TABLE faiss_index_metadata IS 'Metadata for FAISS vector similarity search indexes';
COMMENT ON TABLE voice_auth_sessions IS 'Active voice authentication sessions for tracking multi-step auth flows';
COMMENT ON VIEW voice_auth_statistics IS 'Aggregated statistics for voice authentication attempts';
COMMENT ON VIEW user_voice_profiles IS 'Combined view of users and their voice profile enrollment status';