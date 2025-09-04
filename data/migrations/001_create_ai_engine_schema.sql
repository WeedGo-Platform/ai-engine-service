-- AI Engine Service Database Schema
-- PostgreSQL schema for the WeedGo AI Engine Service

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ai_engine;
CREATE SCHEMA IF NOT EXISTS cannabis_data;
CREATE SCHEMA IF NOT EXISTS customer_analytics;

-- Set search path
SET search_path TO ai_engine, cannabis_data, customer_analytics, public;

-- ================================================
-- CANNABIS PRODUCT DATA TABLES
-- ================================================

-- Main cannabis products table (from OCS data)
CREATE TABLE cannabis_data.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ocs_item_number VARCHAR(50) UNIQUE NOT NULL,
    ocs_variant_number VARCHAR(100) UNIQUE NOT NULL,
    gtin BIGINT,
    
    -- Basic product information
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(200) NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    street_name VARCHAR(500),
    
    -- Categories
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100),
    sub_sub_category VARCHAR(100),
    
    -- Descriptions
    short_description TEXT,
    long_description TEXT,
    
    -- Product specifications
    size VARCHAR(50),
    unit_of_measure VARCHAR(20),
    pack_size DECIMAL(10,2),
    net_weight DECIMAL(10,4),
    color VARCHAR(100),
    
    -- Cannabis-specific content
    thc_min_percent DECIMAL(5,2),
    thc_max_percent DECIMAL(5,2),
    thc_content_per_unit DECIMAL(10,4),
    thc_content_per_volume DECIMAL(10,4),
    thc_min_mg_g DECIMAL(10,4),
    thc_max_mg_g DECIMAL(10,4),
    
    cbd_min_percent DECIMAL(5,2),
    cbd_max_percent DECIMAL(5,2),
    cbd_content_per_unit DECIMAL(10,4),
    cbd_content_per_volume DECIMAL(10,4),
    cbd_min_mg_g DECIMAL(10,4),
    cbd_max_mg_g DECIMAL(10,4),
    
    -- Cannabis characteristics
    plant_type VARCHAR(50),
    dried_flower_equivalency DECIMAL(10,2),
    terpenes TEXT[],
    
    -- Growing information
    growing_method VARCHAR(100),
    grow_medium VARCHAR(100),
    grow_method VARCHAR(100),
    grow_region VARCHAR(200),
    drying_method VARCHAR(100),
    trimming_method VARCHAR(100),
    ontario_grown BOOLEAN DEFAULT FALSE,
    craft BOOLEAN DEFAULT FALSE,
    
    -- Processing information
    extraction_process VARCHAR(200),
    carrier_oil VARCHAR(100),
    
    -- Hardware specifications (for vapes, etc.)
    heating_element_type VARCHAR(100),
    battery_type VARCHAR(100),
    rechargeable_battery BOOLEAN,
    removable_battery BOOLEAN,
    replacement_parts_available BOOLEAN,
    temperature_control BOOLEAN,
    temperature_display BOOLEAN,
    compatibility TEXT,
    
    -- Inventory and logistics
    stock_status VARCHAR(20),
    inventory_status VARCHAR(50),
    items_per_retail_pack INTEGER,
    eaches_per_inner_pack INTEGER,
    eaches_per_master_case INTEGER,
    fulfilment_method VARCHAR(50),
    delivery_tier VARCHAR(50),
    
    -- Physical dimensions
    dimension_width_cm DECIMAL(8,4),
    dimension_height_cm DECIMAL(8,4),
    dimension_depth_cm DECIMAL(8,4),
    dimension_volume_ml DECIMAL(10,4),
    dimension_weight_kg DECIMAL(8,4),
    
    -- Storage and safety
    storage_criteria TEXT,
    food_allergens TEXT[],
    ingredients TEXT[],
    
    -- Media
    image_url TEXT,
    additional_images TEXT[],
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Search vector will be updated via trigger
    search_vector tsvector
);

-- Product categories lookup table
CREATE TABLE cannabis_data.product_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100),
    sub_sub_category VARCHAR(100),
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(category, sub_category, sub_sub_category)
);

-- Product effects and recommendations
CREATE TABLE cannabis_data.product_effects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES cannabis_data.products(id) ON DELETE CASCADE,
    effect_type VARCHAR(50) NOT NULL, -- 'effect', 'medical_use', 'flavor', 'aroma'
    effect_name VARCHAR(200) NOT NULL,
    intensity DECIMAL(3,2), -- 0.0 to 1.0
    confidence DECIMAL(3,2), -- ML model confidence
    source VARCHAR(50), -- 'terpenes', 'strain_data', 'user_reviews', 'ml_prediction'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product pricing history
CREATE TABLE cannabis_data.product_pricing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES cannabis_data.products(id) ON DELETE CASCADE,
    ocs_item_number VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    price_per_gram DECIMAL(10,2),
    discount_percent DECIMAL(5,2),
    promotion_type VARCHAR(100),
    competitor_store VARCHAR(200),
    price_source VARCHAR(100), -- 'ocs', 'competitor_scrape', 'manual'
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================
-- AI/ML MODELS AND EMBEDDINGS
-- ================================================

-- Product embeddings for semantic search
CREATE TABLE ai_engine.product_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES cannabis_data.products(id) ON DELETE CASCADE,
    embedding_type VARCHAR(50) NOT NULL, -- 'description', 'effects', 'terpenes', 'combined'
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    embedding_vector DECIMAL(8,6)[], -- Will store as array, Milvus will handle actual vectors
    vector_dimension INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(product_id, embedding_type, model_name, model_version)
);

-- ML model metadata
CREATE TABLE ai_engine.ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'embedding', 'classification', 'regression', 'recommendation'
    model_version VARCHAR(50) NOT NULL,
    model_path TEXT NOT NULL,
    model_format VARCHAR(20) NOT NULL, -- 'pytorch', 'onnx', 'tensorflow', 'pickle'
    
    -- Model performance metrics
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    
    -- Model configuration
    input_features TEXT[], -- JSON array of feature names
    output_classes TEXT[], -- JSON array of class names
    hyperparameters JSONB,
    training_data_size INTEGER,
    validation_data_size INTEGER,
    
    -- Status and metadata
    status VARCHAR(20) DEFAULT 'training', -- 'training', 'active', 'deprecated', 'failed'
    is_production BOOLEAN DEFAULT FALSE,
    trained_by VARCHAR(100),
    training_started_at TIMESTAMP WITH TIME ZONE,
    training_completed_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(model_name, model_version)
);

-- ================================================
-- CUSTOMER ANALYTICS AND RECOGNITION
-- ================================================

-- Customer recognition data (privacy-preserving)
CREATE TABLE customer_analytics.customer_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL, -- Store/tenant identifier
    
    -- Biometric data (cancelable/revocable templates)
    face_template_hash VARCHAR(128) UNIQUE, -- Hashed cancelable biometric template
    template_version VARCHAR(20) NOT NULL,
    template_algorithm VARCHAR(50) NOT NULL,
    
    -- Recognition metadata
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    visit_count INTEGER DEFAULT 1,
    total_purchase_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Privacy and consent
    consent_given BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP WITH TIME ZONE,
    consent_version VARCHAR(20),
    data_retention_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Demographics (anonymized)
    estimated_age_range VARCHAR(20), -- '18-25', '26-35', etc.
    estimated_gender VARCHAR(20), -- Optional, anonymized
    
    -- Preferences (learned from behavior)
    preferred_categories TEXT[],
    preferred_brands TEXT[],
    thc_preference_range VARCHAR(20), -- 'low', 'medium', 'high'
    cbd_preference_range VARCHAR(20),
    price_sensitivity VARCHAR(20), -- 'budget', 'mid-range', 'premium'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customer visit sessions
CREATE TABLE customer_analytics.visit_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id),
    tenant_id UUID NOT NULL,
    
    -- Session details
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Recognition confidence
    recognition_confidence DECIMAL(5,4),
    recognition_method VARCHAR(50), -- 'face_recognition', 'manual_id', 'loyalty_card'
    
    -- Interaction data
    products_viewed TEXT[], -- Product IDs
    products_purchased TEXT[], -- Product IDs
    total_purchase_amount DECIMAL(10,2),
    
    -- AI interactions
    budtender_conversations INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,
    recommendations_given INTEGER DEFAULT 0,
    recommendations_accepted INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================
-- IDENTITY VERIFICATION
-- ================================================

-- Identity verification sessions
CREATE TABLE ai_engine.identity_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    tenant_id UUID NOT NULL,
    
    -- Document information (no personal data stored)
    document_type VARCHAR(50) NOT NULL, -- 'drivers_license', 'passport', 'provincial_id'
    document_region VARCHAR(50), -- 'ON', 'BC', etc.
    
    -- Verification results
    age_verified BOOLEAN DEFAULT FALSE,
    identity_verified BOOLEAN DEFAULT FALSE,
    face_match_verified BOOLEAN DEFAULT FALSE,
    
    -- Confidence scores
    age_verification_confidence DECIMAL(5,4),
    identity_confidence DECIMAL(5,4),
    face_match_confidence DECIMAL(5,4),
    
    -- Document analysis results
    document_valid BOOLEAN DEFAULT FALSE,
    document_expired BOOLEAN DEFAULT TRUE,
    document_tampered BOOLEAN DEFAULT FALSE,
    
    -- Process metadata
    verification_method VARCHAR(50), -- 'ocr_ml', 'manual_review'
    processing_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'manual_review'
    
    -- Privacy (no actual document images stored)
    document_hash VARCHAR(128), -- Hash of document for duplicate detection
    selfie_hash VARCHAR(128), -- Hash of selfie for duplicate detection
    
    -- Audit trail
    verified_by VARCHAR(100), -- System or operator ID
    verification_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ================================================
-- VIRTUAL BUDTENDER AND CONVERSATIONS
-- ================================================

-- Conversation sessions
CREATE TABLE ai_engine.conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id),
    tenant_id UUID NOT NULL,
    
    -- Session configuration
    language_code VARCHAR(10) DEFAULT 'en', -- 'en', 'fr', 'es', 'pt', 'ar', 'zh'
    personality_mode VARCHAR(50) DEFAULT 'professional', -- 'professional', 'casual', 'expert'
    
    -- Session metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    total_messages INTEGER DEFAULT 0,
    session_rating INTEGER, -- 1-5 stars from customer
    session_feedback TEXT,
    
    -- AI metrics
    average_response_time_ms INTEGER,
    recommendations_made INTEGER DEFAULT 0,
    products_recommended TEXT[], -- Product IDs
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual conversation messages
CREATE TABLE ai_engine.conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES ai_engine.conversation_sessions(id) ON DELETE CASCADE,
    
    -- Message details
    message_order INTEGER NOT NULL,
    sender VARCHAR(20) NOT NULL, -- 'customer', 'budtender', 'system'
    message_text TEXT NOT NULL,
    original_language VARCHAR(10),
    translated_text TEXT, -- If translation was performed
    
    -- AI processing
    intent_detected VARCHAR(100), -- 'product_search', 'effect_inquiry', 'price_question', etc.
    entities_extracted JSONB, -- NLP entities like products, effects, etc.
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    confidence_score DECIMAL(5,4),
    
    -- Response metadata
    response_time_ms INTEGER,
    model_used VARCHAR(100),
    model_version VARCHAR(50),
    
    -- Recommendations in this message
    products_mentioned TEXT[], -- Product IDs mentioned in response
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(session_id, message_order)
);

-- ================================================
-- PRICING INTELLIGENCE
-- ================================================

-- Competitor price tracking
CREATE TABLE ai_engine.competitor_pricing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_match_id UUID, -- Links to our product if match found
    
    -- Competitor information
    competitor_name VARCHAR(200) NOT NULL,
    competitor_url TEXT NOT NULL,
    competitor_product_id VARCHAR(200),
    competitor_sku VARCHAR(200),
    
    -- Product information
    product_name VARCHAR(500) NOT NULL,
    brand VARCHAR(200),
    size VARCHAR(50),
    thc_content VARCHAR(50),
    cbd_content VARCHAR(50),
    
    -- Pricing data
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    price_per_gram DECIMAL(10,2),
    original_price DECIMAL(10,2), -- Before discount
    discount_percent DECIMAL(5,2),
    promotion_text TEXT,
    
    -- Availability
    in_stock BOOLEAN DEFAULT TRUE,
    stock_level VARCHAR(50), -- 'in_stock', 'low_stock', 'out_of_stock'
    
    -- Scraping metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scrape_session_id UUID,
    page_url TEXT,
    data_quality_score DECIMAL(3,2), -- 0.0 to 1.0
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price optimization results
CREATE TABLE ai_engine.pricing_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES cannabis_data.products(id) ON DELETE CASCADE,
    
    -- Current pricing
    current_price DECIMAL(10,2) NOT NULL,
    
    -- Recommendations
    recommended_price DECIMAL(10,2) NOT NULL,
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    
    -- Strategy and reasoning
    pricing_strategy VARCHAR(100) NOT NULL, -- 'competitive', 'premium', 'value', 'penetration'
    algorithm_used VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,4),
    
    -- Market analysis
    competitor_avg_price DECIMAL(10,2),
    competitor_min_price DECIMAL(10,2),
    competitor_max_price DECIMAL(10,2),
    market_position VARCHAR(50), -- 'lowest', 'below_average', 'average', 'above_average', 'highest'
    
    -- Impact predictions
    predicted_demand_change DECIMAL(5,2), -- Percentage change
    predicted_revenue_impact DECIMAL(10,2),
    predicted_margin_impact DECIMAL(5,2),
    
    -- Validity
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by VARCHAR(100), -- Algorithm or user
    applied_at TIMESTAMP WITH TIME ZONE,
    performance_tracked BOOLEAN DEFAULT FALSE
);

-- ================================================
-- INDEXES FOR PERFORMANCE
-- ================================================

-- Product search indexes
CREATE INDEX idx_products_search_vector ON cannabis_data.products USING GIN(search_vector);
CREATE INDEX idx_products_category ON cannabis_data.products(category, sub_category);
CREATE INDEX idx_products_brand ON cannabis_data.products(brand);
CREATE INDEX idx_products_thc_range ON cannabis_data.products(thc_min_percent, thc_max_percent);
CREATE INDEX idx_products_cbd_range ON cannabis_data.products(cbd_min_percent, cbd_max_percent);
CREATE INDEX idx_products_active ON cannabis_data.products(is_active);
CREATE INDEX idx_products_ocs_item ON cannabis_data.products(ocs_item_number);

-- Customer analytics indexes
CREATE INDEX idx_customer_profiles_tenant ON customer_analytics.customer_profiles(tenant_id);
CREATE INDEX idx_customer_profiles_template ON customer_analytics.customer_profiles(face_template_hash);
CREATE INDEX idx_visit_sessions_customer ON customer_analytics.visit_sessions(customer_profile_id);
CREATE INDEX idx_visit_sessions_tenant ON customer_analytics.visit_sessions(tenant_id);

-- Conversation indexes
CREATE INDEX idx_conversation_sessions_customer ON ai_engine.conversation_sessions(customer_profile_id);
CREATE INDEX idx_conversation_sessions_tenant ON ai_engine.conversation_sessions(tenant_id);
CREATE INDEX idx_conversation_messages_session ON ai_engine.conversation_messages(session_id);

-- Pricing indexes
CREATE INDEX idx_competitor_pricing_product ON ai_engine.competitor_pricing(product_match_id);
CREATE INDEX idx_competitor_pricing_scraped ON ai_engine.competitor_pricing(scraped_at);
CREATE INDEX idx_pricing_recommendations_product ON ai_engine.pricing_recommendations(product_id);
CREATE INDEX idx_pricing_recommendations_active ON ai_engine.pricing_recommendations(is_active);

-- ================================================
-- TRIGGERS FOR UPDATED_AT
-- ================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for tables with updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON cannabis_data.products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customer_profiles_updated_at BEFORE UPDATE ON customer_analytics.customer_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- INITIAL DATA AND SETTINGS
-- ================================================

-- Insert default product categories based on OCS data structure
INSERT INTO cannabis_data.product_categories (category, sub_category, sub_sub_category, description) VALUES
('Flower', 'Dried Flower', 'Dried Flower', 'Traditional dried cannabis flower'),
('Flower', 'Pre-Rolls', 'Pre-Rolls', 'Pre-rolled cannabis joints'),
('Edibles', 'Chocolate', 'Chocolate', 'Cannabis-infused chocolate products'),
('Edibles', 'Gummies', 'Gummies', 'Cannabis-infused gummy products'),
('Edibles', 'Beverages', 'Beverages', 'Cannabis-infused drinks'),
('Extracts', 'Vape Cartridges', 'Vape Cartridges', 'Cannabis oil cartridges for vaping'),
('Extracts', 'Concentrates', 'Concentrates', 'Cannabis concentrates and extracts'),
('Topicals', 'Creams', 'Creams', 'Cannabis-infused topical creams'),
('Accessories', 'Vaporizers', 'Vaporizers', 'Cannabis vaporization devices');

-- Insert default ML models placeholders
INSERT INTO ai_engine.ml_models (model_name, model_type, model_version, model_path, model_format, status) VALUES
('cannabis_embedder_v1', 'embedding', '1.0.0', '/models/embeddings/cannabis_embedder_v1.onnx', 'onnx', 'training'),
('strain_classifier_v1', 'classification', '1.0.0', '/models/classification/strain_classifier_v1.onnx', 'onnx', 'training'),
('price_optimizer_v1', 'regression', '1.0.0', '/models/pricing/price_optimizer_v1.pkl', 'pickle', 'training'),
('face_recognizer_v1', 'embedding', '1.0.0', '/models/biometric/face_recognizer_v1.onnx', 'onnx', 'training'),
('budtender_llm_v1', 'generation', '1.0.0', '/models/nlp/budtender_llm_v1', 'pytorch', 'training');

-- Function to update search vector
CREATE OR REPLACE FUNCTION cannabis_data.update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.brand, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.short_description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.long_description, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.street_name, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.terpenes, ' '), '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update search vector
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON cannabis_data.products
    FOR EACH ROW
    EXECUTE FUNCTION cannabis_data.update_search_vector();

COMMIT;