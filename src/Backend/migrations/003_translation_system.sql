-- Translation System Migration
-- Supports multilingual content with caching and context

-- Create translations table for storing translated text
CREATE TABLE IF NOT EXISTS translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_text TEXT NOT NULL,
    source_language VARCHAR(10) DEFAULT 'en',
    target_language VARCHAR(10) NOT NULL,
    translated_text TEXT NOT NULL,
    context VARCHAR(255), -- Context for disambiguating translations (e.g., 'button', 'heading', 'product_description')
    namespace VARCHAR(100), -- Namespace for grouping translations (e.g., 'dashboard', 'products', 'common')
    
    -- Metadata
    usage_count INTEGER DEFAULT 1,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE, -- Human-verified translation
    is_cached BOOLEAN DEFAULT TRUE, -- Whether to cache this translation
    model_version VARCHAR(50), -- Track which AI model was used
    confidence_score DECIMAL(3,2), -- Translation confidence (0.00 to 1.00)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint for efficient lookups
    UNIQUE(source_text, source_language, target_language, context, namespace)
);

-- Create translation_overrides table for manual corrections
CREATE TABLE IF NOT EXISTS translation_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    translation_id UUID REFERENCES translations(id) ON DELETE CASCADE,
    override_text TEXT NOT NULL,
    reason TEXT,
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create translation_batches table for tracking bulk translations
CREATE TABLE IF NOT EXISTS translation_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_key VARCHAR(255) UNIQUE NOT NULL,
    total_items INTEGER NOT NULL,
    completed_items INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    source_language VARCHAR(10) DEFAULT 'en',
    target_language VARCHAR(10) NOT NULL,
    namespace VARCHAR(100),
    metadata JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create translation_batch_items table for individual items in a batch
CREATE TABLE IF NOT EXISTS translation_batch_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES translation_batches(id) ON DELETE CASCADE,
    source_text TEXT NOT NULL,
    translated_text TEXT,
    context VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create supported_languages table
CREATE TABLE IF NOT EXISTS supported_languages (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    native_name VARCHAR(100) NOT NULL,
    is_rtl BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    coverage_percentage DECIMAL(5,2) DEFAULT 0.00, -- Percentage of UI strings translated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert common supported languages
INSERT INTO supported_languages (code, name, native_name, is_rtl) VALUES
    ('en', 'English', 'English', FALSE),
    ('fr', 'French', 'Français', FALSE),
    ('es', 'Spanish', 'Español', FALSE),
    ('de', 'German', 'Deutsch', FALSE),
    ('it', 'Italian', 'Italiano', FALSE),
    ('pt', 'Portuguese', 'Português', FALSE),
    ('nl', 'Dutch', 'Nederlands', FALSE),
    ('ru', 'Russian', 'Русский', FALSE),
    ('zh', 'Chinese', '中文', FALSE),
    ('ja', 'Japanese', '日本語', FALSE),
    ('ko', 'Korean', '한국어', FALSE),
    ('ar', 'Arabic', 'العربية', TRUE),
    ('he', 'Hebrew', 'עברית', TRUE),
    ('hi', 'Hindi', 'हिन्दी', FALSE),
    ('th', 'Thai', 'ไทย', FALSE)
ON CONFLICT (code) DO NOTHING;

-- Create indexes for performance
CREATE INDEX idx_translations_lookup ON translations(source_text, target_language, context, namespace);
CREATE INDEX idx_translations_usage ON translations(usage_count DESC, last_used_at DESC);
CREATE INDEX idx_translations_language ON translations(target_language);
CREATE INDEX idx_translations_verified ON translations(is_verified) WHERE is_verified = TRUE;
CREATE INDEX idx_translations_created ON translations(created_at DESC);

CREATE INDEX idx_batch_items_batch ON translation_batch_items(batch_id);
CREATE INDEX idx_batch_items_status ON translation_batch_items(status);

CREATE INDEX idx_overrides_translation ON translation_overrides(translation_id);
CREATE INDEX idx_overrides_active ON translation_overrides(is_active) WHERE is_active = TRUE;

-- Create function to update usage statistics
CREATE OR REPLACE FUNCTION update_translation_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE translations 
    SET usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_translations_updated_at BEFORE UPDATE ON translations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_overrides_updated_at BEFORE UPDATE ON translation_overrides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for most used translations (for cache warming)
CREATE VIEW v_hot_translations AS
SELECT 
    t.id,
    t.source_text,
    t.source_language,
    t.target_language,
    COALESCE(o.override_text, t.translated_text) as translated_text,
    t.context,
    t.namespace,
    t.usage_count,
    t.last_used_at,
    t.is_verified
FROM translations t
LEFT JOIN translation_overrides o ON t.id = o.translation_id AND o.is_active = TRUE
WHERE t.is_cached = TRUE
ORDER BY t.usage_count DESC, t.last_used_at DESC
LIMIT 1000;

-- Create view for translation statistics
CREATE VIEW v_translation_stats AS
SELECT 
    target_language,
    COUNT(*) as total_translations,
    COUNT(DISTINCT namespace) as namespaces_covered,
    SUM(usage_count) as total_usage,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) FILTER (WHERE is_verified = TRUE) as verified_count,
    MAX(created_at) as last_translation_date
FROM translations
GROUP BY target_language;

-- Add comments for documentation
COMMENT ON TABLE translations IS 'Stores all translations with context and usage statistics';
COMMENT ON TABLE translation_overrides IS 'Manual corrections for AI-generated translations';
COMMENT ON TABLE translation_batches IS 'Tracks bulk translation requests';
COMMENT ON TABLE supported_languages IS 'Languages supported by the translation system';
COMMENT ON VIEW v_hot_translations IS 'Most frequently used translations for cache warming';
COMMENT ON VIEW v_translation_stats IS 'Statistics for translation coverage and usage';