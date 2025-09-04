-- Migration: Create chat_replays table for versioning replay results
-- Purpose: Track AI model improvements over time by storing replay results with versioning

CREATE TABLE IF NOT EXISTS chat_replays (
    id SERIAL PRIMARY KEY,
    
    -- Link to original conversation
    original_conversation_id VARCHAR(255) NOT NULL,
    original_message_id VARCHAR(255),
    original_session_id VARCHAR(255),
    
    -- Replay identification
    replay_session_id VARCHAR(255) NOT NULL,
    replay_batch_id VARCHAR(255), -- Groups all replays from same batch
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Message content
    user_message TEXT NOT NULL,
    original_response TEXT,
    replayed_response TEXT NOT NULL,
    
    -- Performance metrics
    confidence FLOAT,
    original_confidence FLOAT,
    confidence_change FLOAT GENERATED ALWAYS AS (confidence - original_confidence) STORED,
    
    response_time_ms INTEGER,
    original_response_time_ms INTEGER,
    response_time_change_ms INTEGER GENERATED ALWAYS AS (response_time_ms - original_response_time_ms) STORED,
    
    -- Model information
    model_version VARCHAR(50),
    original_model_version VARCHAR(50),
    
    -- Analysis metrics
    improvement_score FLOAT,
    similarity_score FLOAT,
    
    -- Detailed differences (JSON)
    differences JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    replayed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_replay_per_version UNIQUE (original_conversation_id, original_message_id, version)
);

-- Indexes for performance
CREATE INDEX idx_replay_original_conv ON chat_replays(original_conversation_id);
CREATE INDEX idx_replay_version ON chat_replays(version);
CREATE INDEX idx_replay_created ON chat_replays(created_at);
CREATE INDEX idx_replay_batch ON chat_replays(replay_batch_id);
CREATE INDEX idx_replay_session ON chat_replays(replay_session_id);
CREATE INDEX idx_replay_improvement ON chat_replays(improvement_score DESC);
CREATE INDEX idx_replay_confidence_change ON chat_replays(confidence_change DESC);

-- View for easy comparison across versions
CREATE VIEW chat_replay_comparisons AS
SELECT 
    cr1.original_conversation_id,
    cr1.user_message,
    cr1.version as version_1,
    cr1.replayed_response as response_v1,
    cr1.confidence as confidence_v1,
    cr1.response_time_ms as time_v1,
    cr2.version as version_2,
    cr2.replayed_response as response_v2,
    cr2.confidence as confidence_v2,
    cr2.response_time_ms as time_v2,
    (cr2.confidence - cr1.confidence) as confidence_improvement,
    (cr1.response_time_ms - cr2.response_time_ms) as speed_improvement,
    cr2.similarity_score,
    cr2.improvement_score
FROM chat_replays cr1
JOIN chat_replays cr2 
    ON cr1.original_conversation_id = cr2.original_conversation_id 
    AND cr1.original_message_id = cr2.original_message_id
    AND cr1.version < cr2.version
ORDER BY cr1.original_conversation_id, cr1.version;

-- Function to get next version number
CREATE OR REPLACE FUNCTION get_next_replay_version(conv_id VARCHAR, msg_id VARCHAR)
RETURNS INTEGER AS $$
BEGIN
    RETURN COALESCE(
        (SELECT MAX(version) + 1 
         FROM chat_replays 
         WHERE original_conversation_id = conv_id 
           AND original_message_id = msg_id), 
        1
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-set version number
CREATE OR REPLACE FUNCTION set_replay_version()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.version IS NULL OR NEW.version = 0 THEN
        NEW.version := get_next_replay_version(NEW.original_conversation_id, NEW.original_message_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_set_replay_version
BEFORE INSERT ON chat_replays
FOR EACH ROW
EXECUTE FUNCTION set_replay_version();

-- Add foreign key to conversations table (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversations') THEN
        ALTER TABLE chat_replays 
        ADD CONSTRAINT fk_original_conversation 
        FOREIGN KEY (original_conversation_id) 
        REFERENCES conversations(session_id) 
        ON DELETE CASCADE;
    END IF;
END $$;

COMMENT ON TABLE chat_replays IS 'Stores versioned replay results for tracking AI model improvements over time';
COMMENT ON COLUMN chat_replays.version IS 'Version number for this replay of the same original message';
COMMENT ON COLUMN chat_replays.replay_batch_id IS 'Groups all replays from the same replay session';
COMMENT ON COLUMN chat_replays.improvement_score IS 'Calculated score indicating improvement over original response';
COMMENT ON COLUMN chat_replays.similarity_score IS 'Percentage similarity between original and replayed response';