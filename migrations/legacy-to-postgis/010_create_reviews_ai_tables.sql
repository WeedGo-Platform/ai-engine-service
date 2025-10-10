-- ============================================================================
-- Migration: Create Reviews, Ratings & AI/ML Tables
-- Description: Customer reviews, product ratings, and AI/ML infrastructure
-- Dependencies: 009_create_delivery_pricing_tables.sql
-- ============================================================================

-- ===========================
-- REVIEWS & RATINGS TABLES
-- ===========================

-- Customer Reviews
CREATE TABLE IF NOT EXISTS customer_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ocs_sku VARCHAR(50) NOT NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    review_text TEXT,
    pros TEXT,
    cons TEXT,
    is_verified_purchase BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITHOUT TIME ZONE,
    is_featured BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_reviews_user ON customer_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_customer_reviews_sku ON customer_reviews(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_customer_reviews_order ON customer_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_customer_reviews_approved ON customer_reviews(is_approved);
CREATE INDEX IF NOT EXISTS idx_customer_reviews_rating ON customer_reviews(rating);

-- Product Ratings (aggregated)
CREATE TABLE IF NOT EXISTS product_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ocs_sku VARCHAR(50) UNIQUE NOT NULL,
    total_ratings INTEGER DEFAULT 0,
    average_rating NUMERIC(3,2) DEFAULT 0.00,
    five_star_count INTEGER DEFAULT 0,
    four_star_count INTEGER DEFAULT 0,
    three_star_count INTEGER DEFAULT 0,
    two_star_count INTEGER DEFAULT 0,
    one_star_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_ratings_sku ON product_ratings(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_product_ratings_average ON product_ratings(average_rating DESC);

-- Review Attributes (detailed product attribute ratings)
CREATE TABLE IF NOT EXISTS review_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES customer_reviews(id) ON DELETE CASCADE,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_rating INTEGER CHECK (attribute_rating >= 1 AND attribute_rating <= 5),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_attributes_review ON review_attributes(review_id);
CREATE INDEX IF NOT EXISTS idx_review_attributes_name ON review_attributes(attribute_name);

-- Review Media (photos/videos)
CREATE TABLE IF NOT EXISTS review_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES customer_reviews(id) ON DELETE CASCADE,
    media_type VARCHAR(50) NOT NULL,
    media_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_media_review ON review_media(review_id);

-- Review Votes (helpfulness voting)
CREATE TABLE IF NOT EXISTS review_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES customer_reviews(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vote_type VARCHAR(20) NOT NULL CHECK (vote_type IN ('helpful', 'not_helpful')),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(review_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_review_votes_review ON review_votes(review_id);
CREATE INDEX IF NOT EXISTS idx_review_votes_user ON review_votes(user_id);

-- Wishlist
CREATE TABLE IF NOT EXISTS wishlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ocs_sku VARCHAR(50) NOT NULL,
    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    notify_on_sale BOOLEAN DEFAULT true,
    notify_on_restock BOOLEAN DEFAULT true,
    UNIQUE(user_id, ocs_sku)
);

CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist(user_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_sku ON wishlist(ocs_sku);

-- ===========================
-- AI / ML TABLES
-- ===========================

-- AI Conversations
CREATE TABLE IF NOT EXISTS ai_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    store_id UUID REFERENCES stores(id),
    session_id VARCHAR(255) NOT NULL,
    conversation_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITHOUT TIME ZONE,
    total_messages INTEGER DEFAULT 0,
    sentiment_score NUMERIC(3,2),
    conversation_summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_user ON ai_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_session ON ai_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_store ON ai_conversations(store_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_started ON ai_conversations(started_at DESC);

-- Chat Interactions
CREATE TABLE IF NOT EXISTS chat_interactions (
    message_id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES ai_conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(50) NOT NULL,
    sender_id UUID,
    message_text TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    intent VARCHAR(100),
    entities JSONB,
    confidence_score NUMERIC(5,4),
    response_time_ms INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_interactions_conversation ON chat_interactions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_interactions_created ON chat_interactions(created_at DESC);

-- Conversation States
CREATE TABLE IF NOT EXISTS conversation_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID UNIQUE REFERENCES ai_conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    current_step VARCHAR(100),
    context_data JSONB DEFAULT '{}'::jsonb,
    intent_stack JSONB DEFAULT '[]'::jsonb,
    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_states_conversation ON conversation_states(conversation_id);

-- AI Personalities
CREATE TABLE IF NOT EXISTS ai_personalities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    personality_name VARCHAR(255) NOT NULL,
    personality_type VARCHAR(50),
    tone VARCHAR(50),
    greeting_message TEXT,
    system_prompt TEXT,
    response_style JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_personalities_store ON ai_personalities(store_id);
CREATE INDEX IF NOT EXISTS idx_ai_personalities_active ON ai_personalities(is_active);

-- AI Training Data
CREATE TABLE IF NOT EXISTS ai_training_data (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL,
    input_text TEXT NOT NULL,
    expected_output TEXT,
    intent VARCHAR(100),
    entities JSONB,
    context JSONB,
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_training_data_type ON ai_training_data(data_type);
CREATE INDEX IF NOT EXISTS idx_ai_training_data_intent ON ai_training_data(intent);

-- Training Examples
CREATE TABLE IF NOT EXISTS training_examples (
    id SERIAL PRIMARY KEY,
    example_type VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_examples_type ON training_examples(example_type);
CREATE INDEX IF NOT EXISTS idx_training_examples_category ON training_examples(category);

-- Training Sessions
CREATE TABLE IF NOT EXISTS training_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255),
    model_type VARCHAR(100) NOT NULL,
    training_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    training_end TIMESTAMP WITHOUT TIME ZONE,
    epochs INTEGER,
    batch_size INTEGER,
    learning_rate NUMERIC(10,8),
    validation_accuracy NUMERIC(5,4),
    test_accuracy NUMERIC(5,4),
    model_path VARCHAR(500),
    hyperparameters JSONB,
    metrics JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_sessions_model ON training_sessions(model_type);

-- Model Versions
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    training_session_id INTEGER REFERENCES training_sessions(id),
    performance_metrics JSONB,
    is_production BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, version)
);

CREATE INDEX IF NOT EXISTS idx_model_versions_name ON model_versions(model_name);
CREATE INDEX IF NOT EXISTS idx_model_versions_production ON model_versions(is_production);

-- Model Deployments
CREATE TABLE IF NOT EXISTS model_deployments (
    id SERIAL PRIMARY KEY,
    model_version_id INTEGER NOT NULL REFERENCES model_versions(id),
    environment VARCHAR(50) NOT NULL,
    deployment_status VARCHAR(50) DEFAULT 'deploying',
    deployed_at TIMESTAMP WITHOUT TIME ZONE,
    rolled_back_at TIMESTAMP WITHOUT TIME ZONE,
    endpoint_url VARCHAR(500),
    deployment_config JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_deployments_version ON model_deployments(model_version_id);
CREATE INDEX IF NOT EXISTS idx_model_deployments_status ON model_deployments(deployment_status);

-- Model Metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_version_id INTEGER REFERENCES model_versions(id),
    metric_date DATE NOT NULL,
    total_predictions INTEGER DEFAULT 0,
    average_confidence NUMERIC(5,4),
    error_rate NUMERIC(5,4),
    average_response_time_ms INTEGER,
    metrics_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_metrics_version ON model_metrics(model_version_id);
CREATE INDEX IF NOT EXISTS idx_model_metrics_date ON model_metrics(metric_date DESC);

-- Product Recommendations
CREATE TABLE IF NOT EXISTS product_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ocs_sku VARCHAR(50) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,
    score NUMERIC(5,4),
    reason TEXT,
    context JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_product_recommendations_user ON product_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_sku ON product_recommendations(ocs_sku);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_score ON product_recommendations(score DESC);

-- Recommendation Metrics
CREATE TABLE IF NOT EXISTS recommendation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID REFERENCES product_recommendations(id),
    metric_type VARCHAR(50) NOT NULL,
    metric_value NUMERIC(10,2),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendation_metrics_recommendation ON recommendation_metrics(recommendation_id);

-- Parameter Accuracy (ML parameter tracking)
CREATE TABLE IF NOT EXISTS parameter_accuracy (
    id SERIAL PRIMARY KEY,
    parameter_name VARCHAR(255) NOT NULL,
    predicted_value NUMERIC(10,4),
    actual_value NUMERIC(10,4),
    accuracy_score NUMERIC(5,4),
    context JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parameter_accuracy_name ON parameter_accuracy(parameter_name);

-- Conversion Metrics (AI-driven conversion tracking)
CREATE TABLE IF NOT EXISTS conversion_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    conversation_id UUID REFERENCES ai_conversations(id),
    conversion_type VARCHAR(50) NOT NULL,
    converted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    conversion_value NUMERIC(10,2),
    attribution_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversion_metrics_user ON conversion_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_metrics_session ON conversion_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_conversion_metrics_type ON conversion_metrics(conversion_type);

-- Skip Words (NLP stop words)
CREATE TABLE IF NOT EXISTS skip_words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word VARCHAR(100) UNIQUE NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_skip_words_word ON skip_words(word);
CREATE INDEX IF NOT EXISTS idx_skip_words_language ON skip_words(language);

COMMENT ON TABLE customer_reviews IS 'Customer product reviews and ratings';
COMMENT ON TABLE product_ratings IS 'Aggregated product rating statistics';
COMMENT ON TABLE wishlist IS 'User wishlist with notification preferences';
COMMENT ON TABLE ai_conversations IS 'AI chat conversation sessions';
COMMENT ON TABLE chat_interactions IS 'Individual chat messages with NLP metadata';
COMMENT ON TABLE ai_training_data IS 'Training data for AI models';
COMMENT ON TABLE model_versions IS 'ML model version control';
COMMENT ON TABLE product_recommendations IS 'AI-generated product recommendations';
