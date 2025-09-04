-- Multilingual Support Database Schema
-- Supports: English, Spanish, French, Portuguese, Chinese, Arabic

-- Drop existing tables if they exist
DROP TABLE IF EXISTS multilingual_products CASCADE;
DROP TABLE IF EXISTS language_configurations CASCADE;
DROP TABLE IF EXISTS translation_cache CASCADE;
DROP TABLE IF EXISTS customer_language_preferences CASCADE;
DROP TABLE IF EXISTS multilingual_conversations CASCADE;
DROP TABLE IF EXISTS cannabis_terminology CASCADE;
DROP TABLE IF EXISTS language_quality_metrics CASCADE;

-- Language configurations
CREATE TABLE language_configurations (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    native_name VARCHAR(50),
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
    is_rtl BOOLEAN DEFAULT FALSE,  -- Right-to-left (Arabic)
    tokenizer_efficiency FLOAT DEFAULT 1.0,
    model_performance_score FLOAT DEFAULT 0.5,
    fallback_language VARCHAR(10) DEFAULT 'en',
    use_adapter BOOLEAN DEFAULT FALSE,
    adapter_path TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert language configurations
INSERT INTO language_configurations (code, name, native_name, tier, is_rtl, tokenizer_efficiency, model_performance_score, use_adapter) VALUES
('en', 'English', 'English', 1, FALSE, 1.0, 0.95, FALSE),
('es', 'Spanish', 'Español', 1, FALSE, 0.9, 0.85, TRUE),
('fr', 'French', 'Français', 1, FALSE, 0.9, 0.83, TRUE),
('pt', 'Portuguese', 'Português', 2, FALSE, 0.85, 0.78, TRUE),
('zh', 'Chinese', '中文', 3, FALSE, 0.3, 0.60, FALSE),
('ar', 'Arabic', 'العربية', 3, TRUE, 0.4, 0.55, FALSE);

-- Enhanced multilingual products table
CREATE TABLE multilingual_products (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    
    -- English (base language - required)
    name_en TEXT NOT NULL,
    description_en TEXT,
    effects_en TEXT[],
    medical_benefits_en TEXT[],
    warnings_en TEXT,
    
    -- Spanish translations
    name_es TEXT,
    description_es TEXT,
    effects_es TEXT[],
    medical_benefits_es TEXT[],
    warnings_es TEXT,
    
    -- French translations
    name_fr TEXT,
    description_fr TEXT,
    effects_fr TEXT[],
    medical_benefits_fr TEXT[],
    warnings_fr TEXT,
    
    -- Portuguese translations
    name_pt TEXT,
    description_pt TEXT,
    effects_pt TEXT[],
    medical_benefits_pt TEXT[],
    warnings_pt TEXT,
    
    -- Chinese translations
    name_zh TEXT,
    description_zh TEXT,
    effects_zh TEXT[],
    medical_benefits_zh TEXT[],
    warnings_zh TEXT,
    
    -- Arabic translations
    name_ar TEXT,
    description_ar TEXT,
    effects_ar TEXT[],
    medical_benefits_ar TEXT[],
    warnings_ar TEXT,
    
    -- Translation metadata
    translation_status JSONB DEFAULT '{
        "es": "pending",
        "fr": "pending",
        "pt": "pending",
        "zh": "pending",
        "ar": "pending"
    }',
    translation_quality_scores JSONB DEFAULT '{}',
    last_translated_at TIMESTAMP,
    translation_method VARCHAR(50), -- 'human', 'ai', 'hybrid'
    human_verified BOOLEAN DEFAULT FALSE,
    
    -- Search optimization
    search_vectors_en tsvector,
    search_vectors_es tsvector,
    search_vectors_fr tsvector,
    search_vectors_pt tsvector,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(product_id)
);

-- Create indexes for search
CREATE INDEX idx_multilingual_search_en ON multilingual_products USING GIN(search_vectors_en);
CREATE INDEX idx_multilingual_search_es ON multilingual_products USING GIN(search_vectors_es);
CREATE INDEX idx_multilingual_search_fr ON multilingual_products USING GIN(search_vectors_fr);
CREATE INDEX idx_multilingual_search_pt ON multilingual_products USING GIN(search_vectors_pt);

-- Translation cache for dynamic content
CREATE TABLE translation_cache (
    id SERIAL PRIMARY KEY,
    source_text TEXT NOT NULL,
    source_language VARCHAR(10) NOT NULL,
    target_language VARCHAR(10) NOT NULL,
    translated_text TEXT NOT NULL,
    translation_provider VARCHAR(50), -- 'openai', 'google', 'deepl', 'local_model'
    quality_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint for source+languages combination
    UNIQUE(source_text, source_language, target_language)
);

CREATE INDEX idx_translation_cache_lookup ON translation_cache(source_language, target_language, source_text);
CREATE INDEX idx_translation_cache_expiry ON translation_cache(expires_at);

-- Customer language preferences
CREATE TABLE customer_language_preferences (
    customer_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255),
    detected_languages JSONB DEFAULT '[]',
    preferred_language VARCHAR(10) DEFAULT 'en',
    ui_language VARCHAR(10) DEFAULT 'en',
    content_language VARCHAR(10) DEFAULT 'en',
    auto_detect BOOLEAN DEFAULT TRUE,
    language_confidence FLOAT,
    detection_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_lang_session ON customer_language_preferences(session_id);

-- Multilingual conversation history
CREATE TABLE multilingual_conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255),
    
    -- Original message
    message_original TEXT NOT NULL,
    message_language VARCHAR(10) NOT NULL,
    message_confidence FLOAT,
    
    -- Translation if needed
    message_translated TEXT,
    translation_used BOOLEAN DEFAULT FALSE,
    
    -- Response
    response_text TEXT NOT NULL,
    response_language VARCHAR(10) NOT NULL,
    response_translated TEXT,
    
    -- Intent and context
    detected_intent VARCHAR(100),
    cannabis_entities JSONB DEFAULT '{}',
    
    -- Quality metrics
    quality_score FLOAT,
    language_quality_score FLOAT,
    cannabis_accuracy_score FLOAT,
    
    -- Model information
    model_used VARCHAR(100),
    adapter_used VARCHAR(100),
    fallback_used BOOLEAN DEFAULT FALSE,
    
    -- Timing
    processing_time_ms INTEGER,
    translation_time_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_multilingual_conv_session ON multilingual_conversations(session_id, created_at DESC);
CREATE INDEX idx_multilingual_conv_language ON multilingual_conversations(message_language, response_language);

-- Cannabis terminology translations
CREATE TABLE cannabis_terminology (
    id SERIAL PRIMARY KEY,
    term_key VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'strain', 'product', 'effect', 'measurement', 'slang'
    
    -- Translations
    term_en TEXT NOT NULL,
    term_es TEXT,
    term_fr TEXT,
    term_pt TEXT,
    term_zh TEXT,
    term_ar TEXT,
    
    -- Context and usage
    context_notes TEXT,
    is_formal BOOLEAN DEFAULT TRUE,
    is_medical BOOLEAN DEFAULT FALSE,
    is_slang BOOLEAN DEFAULT FALSE,
    
    -- Regulatory flags
    requires_age_warning BOOLEAN DEFAULT FALSE,
    restricted_regions TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(term_key, category)
);

CREATE INDEX idx_cannabis_terms_category ON cannabis_terminology(category);

-- Language quality metrics
CREATE TABLE language_quality_metrics (
    id SERIAL PRIMARY KEY,
    language_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    
    -- Performance metrics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    fallback_count INTEGER DEFAULT 0,
    translation_count INTEGER DEFAULT 0,
    
    -- Quality scores
    avg_quality_score FLOAT,
    avg_response_time_ms FLOAT,
    avg_translation_time_ms FLOAT,
    
    -- User satisfaction
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,
    
    -- Error tracking
    error_count INTEGER DEFAULT 0,
    error_types JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(language_code, date)
);

CREATE INDEX idx_quality_metrics_date ON language_quality_metrics(date DESC);

-- Insert initial cannabis terminology
INSERT INTO cannabis_terminology (term_key, category, term_en, term_es, term_fr, term_pt, term_zh, term_ar) VALUES
-- Strains (usually kept in English globally)
('sativa', 'strain', 'Sativa', 'Sativa', 'Sativa', 'Sativa', 'Sativa', 'ساتيفا'),
('indica', 'strain', 'Indica', 'Indica', 'Indica', 'Indica', 'Indica', 'إنديكا'),
('hybrid', 'strain', 'Hybrid', 'Híbrido', 'Hybride', 'Híbrido', '混合', 'هجين'),

-- Products
('flower', 'product', 'Flower', 'Flor', 'Fleur', 'Flor', '花', 'زهرة'),
('pre_roll', 'product', 'Pre-Roll', 'Pre-Enrollado', 'Pré-Roulé', 'Pré-Enrolado', '预卷烟', 'ملفوف مسبقا'),
('edibles', 'product', 'Edibles', 'Comestibles', 'Comestibles', 'Comestíveis', '食用品', 'مأكولات'),
('vape', 'product', 'Vape', 'Vaporizador', 'Vaporisateur', 'Vaporizador', '电子烟', 'بخار'),
('concentrate', 'product', 'Concentrate', 'Concentrado', 'Concentré', 'Concentrado', '浓缩物', 'مركز'),
('topical', 'product', 'Topical', 'Tópico', 'Topique', 'Tópico', '外用', 'موضعي'),

-- Effects
('relaxing', 'effect', 'Relaxing', 'Relajante', 'Relaxant', 'Relaxante', '放松', 'مريح'),
('energizing', 'effect', 'Energizing', 'Energizante', 'Énergisant', 'Energizante', '提神', 'منشط'),
('euphoric', 'effect', 'Euphoric', 'Eufórico', 'Euphorique', 'Eufórico', '欣快', 'نشوة'),
('creative', 'effect', 'Creative', 'Creativo', 'Créatif', 'Criativo', '创造性', 'إبداعي'),
('focused', 'effect', 'Focused', 'Enfocado', 'Concentré', 'Focado', '专注', 'مركز'),
('sleepy', 'effect', 'Sleepy', 'Somnoliento', 'Somnolent', 'Sonolento', '困倦', 'نعسان'),

-- Measurements
('gram', 'measurement', 'Gram', 'Gramo', 'Gramme', 'Grama', '克', 'جرام'),
('eighth', 'measurement', 'Eighth (3.5g)', 'Octavo (3.5g)', 'Huitième (3.5g)', 'Oitavo (3.5g)', '八分之一(3.5克)', 'ثمن (3.5 جرام)'),
('quarter', 'measurement', 'Quarter (7g)', 'Cuarto (7g)', 'Quart (7g)', 'Quarto (7g)', '四分之一(7克)', 'ربع (7 جرام)'),
('half_ounce', 'measurement', 'Half Ounce (14g)', 'Media Onza (14g)', 'Demi-Once (14g)', 'Meia Onça (14g)', '半盎司(14克)', 'نصف أونصة (14 جرام)'),
('ounce', 'measurement', 'Ounce (28g)', 'Onza (28g)', 'Once (28g)', 'Onça (28g)', '盎司(28克)', 'أونصة (28 جرام)');

-- Create function to update search vectors
CREATE OR REPLACE FUNCTION update_search_vectors() RETURNS trigger AS $$
BEGIN
    NEW.search_vectors_en := to_tsvector('english', COALESCE(NEW.name_en, '') || ' ' || COALESCE(NEW.description_en, ''));
    NEW.search_vectors_es := to_tsvector('spanish', COALESCE(NEW.name_es, '') || ' ' || COALESCE(NEW.description_es, ''));
    NEW.search_vectors_fr := to_tsvector('french', COALESCE(NEW.name_fr, '') || ' ' || COALESCE(NEW.description_fr, ''));
    NEW.search_vectors_pt := to_tsvector('portuguese', COALESCE(NEW.name_pt, '') || ' ' || COALESCE(NEW.description_pt, ''));
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for search vectors
CREATE TRIGGER update_multilingual_search_vectors
    BEFORE INSERT OR UPDATE ON multilingual_products
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vectors();