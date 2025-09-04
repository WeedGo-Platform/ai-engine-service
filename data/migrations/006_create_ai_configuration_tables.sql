-- Create comprehensive AI configuration tables for dynamic system behavior
-- This replaces hardcoded values throughout the AI engine

-- 1. Medical Intents Configuration
CREATE TABLE IF NOT EXISTS medical_intents (
    id SERIAL PRIMARY KEY,
    intent_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    search_query VARCHAR(100), -- What to search for when this intent is detected
    active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100, -- Higher priority intents are checked first
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords associated with each medical intent
CREATE TABLE IF NOT EXISTS medical_intent_keywords (
    id SERIAL PRIMARY KEY,
    intent_id INTEGER REFERENCES medical_intents(id) ON DELETE CASCADE,
    keyword VARCHAR(50) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0, -- Keyword importance (0.0 to 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(intent_id, keyword)
);

-- 2. Product Categories Configuration
CREATE TABLE IF NOT EXISTS product_category_config (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    priority INTEGER DEFAULT 100,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords for detecting product categories
CREATE TABLE IF NOT EXISTS category_keywords (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES product_category_config(id) ON DELETE CASCADE,
    keyword VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, keyword)
);

-- 3. Strain Types Configuration
CREATE TABLE IF NOT EXISTS strain_types (
    id SERIAL PRIMARY KEY,
    strain_type VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    typical_effects TEXT[],
    recommended_for TEXT[],
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. AI Response Templates
CREATE TABLE IF NOT EXISTS response_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    scenario VARCHAR(100), -- greeting, no_products_found, product_found, etc.
    template_text TEXT NOT NULL,
    personality_id VARCHAR(50), -- Link to specific personality or NULL for generic
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. System Configuration Parameters
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50), -- string, integer, boolean, json
    category VARCHAR(50), -- search, response, model, etc.
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default medical intents
INSERT INTO medical_intents (intent_name, description, search_query) VALUES
('pain', 'Pain relief and management', 'cbd'),
('anxiety', 'Anxiety and stress relief', 'cbd'),
('sleep', 'Sleep and insomnia help', 'indica'),
('relief', 'General therapeutic relief', 'cbd'),
('energy', 'Energy and focus', 'sativa'),
('appetite', 'Appetite stimulation', 'indica'),
('nausea', 'Nausea relief', 'hybrid')
ON CONFLICT (intent_name) DO NOTHING;

-- Insert medical intent keywords
INSERT INTO medical_intent_keywords (intent_id, keyword, weight)
SELECT m.id, k.keyword, k.weight
FROM medical_intents m
CROSS JOIN (VALUES
    ('pain', 'pain', 1.0),
    ('pain', 'ache', 0.9),
    ('pain', 'hurt', 0.9),
    ('pain', 'sore', 0.8),
    ('pain', 'inflammation', 0.9),
    ('anxiety', 'anxiety', 1.0),
    ('anxiety', 'anxious', 0.9),
    ('anxiety', 'stress', 0.9),
    ('anxiety', 'stressed', 0.9),
    ('anxiety', 'nervous', 0.8),
    ('anxiety', 'panic', 0.9),
    ('sleep', 'sleep', 1.0),
    ('sleep', 'insomnia', 1.0),
    ('sleep', 'rest', 0.8),
    ('sleep', 'tired', 0.7),
    ('sleep', 'bedtime', 0.9),
    ('relief', 'relief', 1.0),
    ('relief', 'help', 0.7),
    ('relief', 'therapy', 0.9),
    ('relief', 'medical', 0.9),
    ('relief', 'treatment', 0.9),
    ('energy', 'energy', 1.0),
    ('energy', 'energetic', 0.9),
    ('energy', 'focus', 0.9),
    ('energy', 'creative', 0.8),
    ('energy', 'productivity', 0.8),
    ('appetite', 'appetite', 1.0),
    ('appetite', 'hungry', 0.8),
    ('appetite', 'munchies', 0.9),
    ('appetite', 'eating', 0.7),
    ('nausea', 'nausea', 1.0),
    ('nausea', 'nauseous', 0.9),
    ('nausea', 'sick', 0.7),
    ('nausea', 'queasy', 0.8)
) AS k(intent_name, keyword, weight)
WHERE m.intent_name = k.intent_name
ON CONFLICT (intent_id, keyword) DO NOTHING;

-- Insert product categories
INSERT INTO product_category_config (category_name, display_name, description) VALUES
('flower', 'Flower', 'Cannabis flower and buds'),
('edibles', 'Edibles', 'Cannabis-infused food products'),
('vapes', 'Vapes', 'Vaporizer cartridges and pens'),
('extracts', 'Extracts', 'Concentrates and extracts'),
('pre-rolls', 'Pre-Rolls', 'Pre-rolled joints'),
('topicals', 'Topicals', 'Creams and lotions'),
('accessories', 'Accessories', 'Rolling papers, grinders, etc.')
ON CONFLICT (category_name) DO NOTHING;

-- Insert category keywords
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, k.keyword
FROM product_category_config c
CROSS JOIN (VALUES
    ('flower', 'flower'),
    ('flower', 'bud'),
    ('flower', 'nugs'),
    ('flower', 'buds'),
    ('edibles', 'edible'),
    ('edibles', 'gummy'),
    ('edibles', 'chocolate'),
    ('edibles', 'candy'),
    ('edibles', 'cookie'),
    ('vapes', 'vape'),
    ('vapes', 'cart'),
    ('vapes', 'cartridge'),
    ('vapes', 'pen'),
    ('extracts', 'dab'),
    ('extracts', 'shatter'),
    ('extracts', 'wax'),
    ('extracts', 'concentrate'),
    ('extracts', 'oil'),
    ('extracts', 'rosin'),
    ('pre-rolls', 'preroll'),
    ('pre-rolls', 'joint'),
    ('pre-rolls', 'blunt'),
    ('topicals', 'cream'),
    ('topicals', 'lotion'),
    ('topicals', 'balm'),
    ('accessories', 'papers'),
    ('accessories', 'grinder'),
    ('accessories', 'pipe')
) AS k(category_name, keyword)
WHERE c.category_name = k.category_name
ON CONFLICT (category_id, keyword) DO NOTHING;

-- Insert strain types
INSERT INTO strain_types (strain_type, description, typical_effects, recommended_for) VALUES
('sativa', 'Energizing and uplifting', 
 ARRAY['energy', 'focus', 'creativity', 'euphoria'], 
 ARRAY['daytime use', 'social activities', 'creative projects']),
('indica', 'Relaxing and sedating', 
 ARRAY['relaxation', 'sleep', 'pain relief', 'calm'], 
 ARRAY['nighttime use', 'pain management', 'insomnia']),
('hybrid', 'Balanced effects', 
 ARRAY['balanced', 'versatile', 'mild euphoria'], 
 ARRAY['anytime use', 'first-time users', 'versatile needs']),
('cbd', 'Non-psychoactive therapeutic', 
 ARRAY['relief', 'calm', 'clarity', 'therapeutic'], 
 ARRAY['medical use', 'anxiety', 'pain', 'inflammation'])
ON CONFLICT (strain_type) DO NOTHING;

-- Insert response templates
INSERT INTO response_templates (template_name, scenario, template_text) VALUES
('greeting_new', 'greeting', 'Welcome! I''m here to help you find the perfect cannabis products. What are you looking for today?'),
('greeting_returning', 'greeting', 'Welcome back! Great to see you again. What can I help you find today?'),
('no_products', 'no_products_found', 'I couldn''t find exact matches for that, but let me show you some alternatives that might work.'),
('products_found', 'product_found', 'I found {count} great options for you. Here are my top recommendations:'),
('medical_response', 'medical_intent', 'I understand you''re looking for {intent} relief. Here are some products that might help:'),
('error_response', 'error', 'I''m having a moment. Let me try to help you another way.')
ON CONFLICT (template_name) DO NOTHING;

-- Insert system configuration
INSERT INTO system_config (config_key, config_value, config_type, category, description) VALUES
('max_search_words', '3', 'integer', 'search', 'Maximum words to use in product search'),
('fallback_search_enabled', 'true', 'boolean', 'search', 'Enable fallback search when no results found'),
('min_word_length', '2', 'integer', 'search', 'Minimum word length for search terms'),
('response_max_length', '100', 'integer', 'response', 'Maximum words in AI response'),
('confidence_threshold', '0.5', 'decimal', 'response', 'Minimum confidence score for responses'),
('products_per_response', '3', 'integer', 'response', 'Number of products to show in response'),
('cache_ttl_seconds', '300', 'integer', 'cache', 'Cache time-to-live in seconds'),
('model_temperature', '0.7', 'decimal', 'model', 'AI model temperature setting'),
('model_max_tokens', '150', 'integer', 'model', 'Maximum tokens for model response')
ON CONFLICT (config_key) DO NOTHING;

-- Create update triggers
CREATE OR REPLACE FUNCTION update_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_medical_intents_timestamp
BEFORE UPDATE ON medical_intents
FOR EACH ROW EXECUTE FUNCTION update_config_timestamp();

CREATE TRIGGER update_category_config_timestamp
BEFORE UPDATE ON product_category_config
FOR EACH ROW EXECUTE FUNCTION update_config_timestamp();

CREATE TRIGGER update_strain_types_timestamp
BEFORE UPDATE ON strain_types
FOR EACH ROW EXECUTE FUNCTION update_config_timestamp();

CREATE TRIGGER update_templates_timestamp
BEFORE UPDATE ON response_templates
FOR EACH ROW EXECUTE FUNCTION update_config_timestamp();

CREATE TRIGGER update_system_config_timestamp
BEFORE UPDATE ON system_config
FOR EACH ROW EXECUTE FUNCTION update_config_timestamp();

-- Create indexes for performance
CREATE INDEX idx_medical_keywords_intent ON medical_intent_keywords(intent_id);
CREATE INDEX idx_category_keywords_category ON category_keywords(category_id);
CREATE INDEX idx_templates_scenario ON response_templates(scenario);
CREATE INDEX idx_system_config_category ON system_config(category);
CREATE INDEX idx_system_config_active ON system_config(active);