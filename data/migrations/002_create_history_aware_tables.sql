-- History-Aware Budtender Extension Schema
-- Additional tables for customer purchase history and conversation intelligence

-- Enable required extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set search path
SET search_path TO ai_engine, cannabis_data, customer_analytics, public;

-- ================================================
-- CUSTOMER PURCHASE HISTORY AND PREFERENCES
-- ================================================

-- Customer purchase transactions
CREATE TABLE customer_analytics.purchase_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id) ON DELETE CASCADE,
    visit_session_id UUID REFERENCES customer_analytics.visit_sessions(id),
    tenant_id UUID NOT NULL,
    
    -- Purchase details
    product_id UUID REFERENCES cannabis_data.products(id),
    ocs_item_number VARCHAR(50) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    brand VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100),
    
    -- Purchase specifics
    quantity_purchased DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    
    -- Product characteristics at time of purchase
    thc_content DECIMAL(5,2),
    cbd_content DECIMAL(5,2),
    plant_type VARCHAR(50),
    terpenes TEXT[],
    
    -- Purchase context
    purchase_reason VARCHAR(100), -- 'recommendation', 'repeat_purchase', 'explore', 'price_deal'
    recommendation_source VARCHAR(50), -- 'budtender_ai', 'staff', 'self_selected'
    customer_satisfaction INTEGER, -- 1-5 rating if provided
    
    -- Metadata
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learned customer preferences from behavior analysis
CREATE TABLE customer_analytics.customer_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id) ON DELETE CASCADE,
    
    -- Category preferences (learned from purchases)
    preferred_categories JSONB, -- {"Flower": 0.7, "Edibles": 0.3}
    preferred_brands JSONB, -- {"Brand A": 0.6, "Brand B": 0.4}
    preferred_plant_types JSONB, -- {"Indica": 0.5, "Hybrid": 0.3, "Sativa": 0.2}
    
    -- Potency preferences
    preferred_thc_range_min DECIMAL(5,2),
    preferred_thc_range_max DECIMAL(5,2),
    preferred_cbd_range_min DECIMAL(5,2),
    preferred_cbd_range_max DECIMAL(5,2),
    
    -- Price sensitivity analysis
    average_purchase_amount DECIMAL(10,2),
    price_sensitivity_score DECIMAL(3,2), -- 0.0 (budget-conscious) to 1.0 (premium-focused)
    
    -- Behavioral patterns
    purchase_frequency_days DECIMAL(5,1), -- Average days between purchases
    variety_seeking_score DECIMAL(3,2), -- 0.0 (consistent) to 1.0 (always trying new)
    recommendation_acceptance_rate DECIMAL(3,2), -- How often they buy recommended products
    
    -- Expertise level
    expertise_level VARCHAR(20) DEFAULT 'novice', -- 'novice', 'intermediate', 'expert'
    expertise_indicators JSONB, -- Factors that led to expertise classification
    
    -- Terpene preferences (if customer shows pattern)
    preferred_terpenes JSONB, -- {"limonene": 0.8, "myrcene": 0.6}
    
    -- Situational preferences
    day_time_preferences JSONB, -- Different preferences by time of day
    seasonal_preferences JSONB, -- Different preferences by season
    
    -- Conversation preferences
    preferred_interaction_style VARCHAR(20) DEFAULT 'guided', -- 'guided', 'direct', 'exploratory'
    wants_detailed_explanations BOOLEAN DEFAULT TRUE,
    
    -- Model metadata
    confidence_score DECIMAL(3,2) DEFAULT 0.0, -- How confident we are in these preferences
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(20) DEFAULT '1.0',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================
-- CONVERSATION STATE AND FLOW MANAGEMENT
-- ================================================

-- Enhanced conversation session with flow state
CREATE TABLE ai_engine.conversation_sessions_enhanced (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id),
    tenant_id UUID NOT NULL,
    
    -- Conversation flow state
    current_flow_stage VARCHAR(50) DEFAULT 'greeting', -- 'greeting', 'category', 'subcategory', 'effects', 'potency', 'size_brand', 'final_selection'
    flow_progress JSONB DEFAULT '{}', -- Track selections made at each stage
    conversation_goal VARCHAR(50), -- 'product_search', 'education', 'exploration', 'repeat_purchase'
    
    -- Customer context
    detected_expertise_level VARCHAR(20), -- 'novice', 'intermediate', 'expert'
    is_returning_customer BOOLEAN DEFAULT FALSE,
    last_purchase_days_ago INTEGER,
    preferred_interaction_style VARCHAR(20), -- Based on customer history or detection
    
    -- Current search context
    active_filters JSONB DEFAULT '{}', -- Current filter state
    products_shown_ids TEXT[], -- Products already shown to avoid repetition
    rejected_suggestions TEXT[], -- Products customer showed no interest in
    
    -- Adaptive behavior
    adaptation_context JSONB DEFAULT '{}', -- Context for personalizing responses
    response_complexity_level VARCHAR(20) DEFAULT 'medium', -- 'simple', 'medium', 'detailed'
    
    -- Session configuration
    language_code VARCHAR(10) DEFAULT 'en',
    personality_mode VARCHAR(50) DEFAULT 'professional',
    
    -- Session metadata  
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    total_messages INTEGER DEFAULT 0,
    session_rating INTEGER,
    session_feedback TEXT,
    
    -- AI metrics
    average_response_time_ms INTEGER,
    recommendations_made INTEGER DEFAULT 0,
    products_recommended TEXT[],
    successful_conversion BOOLEAN DEFAULT FALSE, -- Did they find what they wanted?
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversation flow steps and branching logic
CREATE TABLE ai_engine.conversation_flow_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES ai_engine.conversation_sessions_enhanced(id) ON DELETE CASCADE,
    
    -- Step details
    step_order INTEGER NOT NULL,
    flow_stage VARCHAR(50) NOT NULL, -- Links to current_flow_stage
    step_type VARCHAR(30) NOT NULL, -- 'question', 'filter', 'presentation', 'clarification'
    
    -- Step content
    question_asked TEXT,
    options_presented JSONB, -- Categories, effects, etc. shown to customer
    customer_response TEXT,
    
    -- Processing results
    extracted_intent JSONB, -- What we understood from their response
    applied_filters JSONB, -- Filters applied based on this step
    
    -- Flow control
    next_suggested_stage VARCHAR(50), -- Where to go next
    branching_logic JSONB, -- Why this path was chosen
    
    -- Timing
    step_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    step_completed_at TIMESTAMP WITH TIME ZONE,
    response_time_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(session_id, step_order)
);

-- ================================================
-- PRODUCT INTERACTION TRACKING
-- ================================================

-- Track detailed customer interactions with products
CREATE TABLE customer_analytics.product_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id),
    session_id UUID REFERENCES ai_engine.conversation_sessions_enhanced(id),
    product_id UUID REFERENCES cannabis_data.products(id),
    
    -- Interaction details
    interaction_type VARCHAR(30) NOT NULL, -- 'viewed', 'shown_details', 'added_to_consideration', 'rejected', 'purchased'
    interaction_context VARCHAR(50), -- 'recommendation', 'search_result', 'related_product', 'repeat_suggestion'
    
    -- Engagement metrics
    time_spent_viewing_seconds INTEGER,
    details_requested BOOLEAN DEFAULT FALSE,
    comparison_requested BOOLEAN DEFAULT FALSE,
    
    -- Customer feedback on product
    customer_interest_level INTEGER, -- 1-5 scale if expressed
    rejection_reason VARCHAR(100), -- 'too_expensive', 'wrong_effects', 'wrong_potency', etc.
    
    -- Recommendation context
    was_recommended BOOLEAN DEFAULT FALSE,
    recommendation_reason TEXT, -- Why this product was suggested
    recommendation_algorithm VARCHAR(50), -- Which algorithm suggested it
    
    -- Metadata
    interaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================
-- EXPERTISE AND PERSONALIZATION MODELS
-- ================================================

-- Customer expertise indicators and scoring
CREATE TABLE customer_analytics.expertise_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id) ON DELETE CASCADE,
    
    -- Vocabulary sophistication
    uses_strain_names BOOLEAN DEFAULT FALSE,
    uses_terpene_terminology BOOLEAN DEFAULT FALSE,
    uses_technical_terms BOOLEAN DEFAULT FALSE,
    
    -- Purchase behavior indicators
    explores_variety BOOLEAN DEFAULT FALSE, -- Tries many different products
    has_specific_preferences BOOLEAN DEFAULT FALSE, -- Consistent in choices
    asks_detailed_questions BOOLEAN DEFAULT FALSE,
    
    -- Interaction patterns
    total_conversations INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    average_session_length_minutes DECIMAL(5,1),
    
    -- Knowledge demonstration
    provides_product_feedback BOOLEAN DEFAULT FALSE,
    asks_about_cultivation BOOLEAN DEFAULT FALSE,
    discusses_effects_detailed BOOLEAN DEFAULT FALSE,
    
    -- Calculated expertise score
    expertise_score DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    expertise_level VARCHAR(20) DEFAULT 'novice',
    
    -- Confidence and metadata
    calculation_confidence DECIMAL(3,2) DEFAULT 0.0,
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(20) DEFAULT '1.0',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Personalization rules and recommendations
CREATE TABLE ai_engine.personalization_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'conversation_flow', 'product_filter', 'response_style', 'recommendation_logic'
    
    -- Trigger conditions
    trigger_conditions JSONB NOT NULL, -- When this rule applies
    expertise_level_filter VARCHAR(20), -- Which expertise levels this applies to
    
    -- Rule logic
    rule_logic JSONB NOT NULL, -- What changes to make
    priority INTEGER DEFAULT 100, -- Higher priority rules override lower
    
    -- Effectiveness tracking
    times_applied INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2), -- How often this rule leads to positive outcomes
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(rule_name)
);

-- ================================================
-- CONVERSATION INTELLIGENCE AND ANALYTICS
-- ================================================

-- Customer journey mapping and funnel analysis
CREATE TABLE customer_analytics.customer_journey_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_profile_id UUID REFERENCES customer_analytics.customer_profiles(id) ON DELETE CASCADE,
    session_id UUID REFERENCES ai_engine.conversation_sessions_enhanced(id),
    
    -- Journey stage
    stage_name VARCHAR(50) NOT NULL, -- 'awareness', 'consideration', 'decision', 'purchase', 'advocacy'
    stage_entered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stage_duration_seconds INTEGER,
    
    -- Stage context
    trigger_event VARCHAR(100), -- What moved them to this stage
    stage_sentiment DECIMAL(3,2), -- Customer sentiment during this stage
    
    -- Conversion metrics
    converted_to_next_stage BOOLEAN DEFAULT FALSE,
    conversion_trigger VARCHAR(100),
    
    -- Friction points
    friction_indicators JSONB, -- Hesitation, confusion, etc.
    support_provided VARCHAR(200), -- How we helped in this stage
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================
-- INDEXES FOR PERFORMANCE
-- ================================================

-- Purchase history indexes
CREATE INDEX idx_purchase_history_customer ON customer_analytics.purchase_history(customer_profile_id);
CREATE INDEX idx_purchase_history_product ON customer_analytics.purchase_history(product_id);
CREATE INDEX idx_purchase_history_date ON customer_analytics.purchase_history(purchased_at);
CREATE INDEX idx_purchase_history_category ON customer_analytics.purchase_history(category);

-- Customer preferences indexes
CREATE INDEX idx_customer_preferences_profile ON customer_analytics.customer_preferences(customer_profile_id);
CREATE INDEX idx_customer_preferences_expertise ON customer_analytics.customer_preferences(expertise_level);

-- Conversation flow indexes
CREATE INDEX idx_conversation_enhanced_customer ON ai_engine.conversation_sessions_enhanced(customer_profile_id);
CREATE INDEX idx_conversation_enhanced_stage ON ai_engine.conversation_sessions_enhanced(current_flow_stage);
CREATE INDEX idx_conversation_flow_steps_session ON ai_engine.conversation_flow_steps(session_id);

-- Product interaction indexes
CREATE INDEX idx_product_interactions_customer ON customer_analytics.product_interactions(customer_profile_id);
CREATE INDEX idx_product_interactions_product ON customer_analytics.product_interactions(product_id);
CREATE INDEX idx_product_interactions_type ON customer_analytics.product_interactions(interaction_type);

-- Expertise indicators indexes
CREATE INDEX idx_expertise_indicators_customer ON customer_analytics.expertise_indicators(customer_profile_id);
CREATE INDEX idx_expertise_indicators_level ON customer_analytics.expertise_indicators(expertise_level);

-- Journey stages indexes
CREATE INDEX idx_journey_stages_customer ON customer_analytics.customer_journey_stages(customer_profile_id);
CREATE INDEX idx_journey_stages_stage ON customer_analytics.customer_journey_stages(stage_name);

-- ================================================
-- TRIGGERS FOR UPDATED_AT
-- ================================================

-- Add triggers for tables with updated_at or last_modified fields
CREATE TRIGGER update_customer_preferences_updated_at BEFORE UPDATE ON customer_analytics.customer_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update last_modified timestamp
CREATE OR REPLACE FUNCTION update_last_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_personalization_rules_last_modified BEFORE UPDATE ON ai_engine.personalization_rules
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_column();

-- ================================================
-- INITIAL PERSONALIZATION RULES
-- ================================================

-- Insert default personalization rules
INSERT INTO ai_engine.personalization_rules (rule_name, rule_type, trigger_conditions, expertise_level_filter, rule_logic, priority) VALUES

-- Flow rules for different expertise levels
('novice_guided_flow', 'conversation_flow', 
 '{"expertise_level": "novice", "is_new_customer": true}', 
 'novice',
 '{"flow_style": "guided", "show_explanations": true, "limit_options": 5, "include_education": true}',
 100),

('expert_direct_flow', 'conversation_flow',
 '{"expertise_level": "expert"}',
 'expert', 
 '{"flow_style": "direct", "show_explanations": false, "limit_options": 10, "skip_basic_questions": true}',
 100),

-- Recommendation rules based on purchase history
('repeat_customer_shortcuts', 'conversation_flow',
 '{"has_purchase_history": true, "last_purchase_days": {"$lt": 30}}',
 null,
 '{"offer_repeat_purchase": true, "show_similar_products": true, "remember_preferences": true}',
 90),

-- Product filtering rules
('price_conscious_filter', 'product_filter',
 '{"price_sensitivity_score": {"$lt": 0.3}}',
 null,
 '{"sort_by_price": true, "highlight_deals": true, "filter_premium": true}',
 80),

('variety_seeker_filter', 'product_filter',
 '{"variety_seeking_score": {"$gt": 0.7}}',
 null,
 '{"exclude_recent_purchases": true, "promote_new_products": true, "diverse_recommendations": true}',
 80);

-- ================================================
-- VIEWS FOR EASY ACCESS
-- ================================================

-- Customer summary view combining profile, preferences, and history
CREATE VIEW customer_analytics.customer_summary AS
SELECT 
    cp.id as customer_id,
    cp.tenant_id,
    cp.visit_count,
    cp.total_purchase_amount,
    cp.first_seen_at,
    cp.last_seen_at,
    
    -- Preferences
    cpf.expertise_level,
    cpf.preferred_categories,
    cpf.preferred_brands,
    cpf.average_purchase_amount,
    cpf.variety_seeking_score,
    cpf.recommendation_acceptance_rate,
    
    -- Recent activity
    COUNT(ph.id) as total_purchases,
    MAX(ph.purchased_at) as last_purchase_date,
    AVG(ph.total_amount) as avg_purchase_amount,
    
    -- Expertise indicators
    ei.expertise_score,
    ei.uses_strain_names,
    ei.uses_terpene_terminology
    
FROM customer_analytics.customer_profiles cp
LEFT JOIN customer_analytics.customer_preferences cpf ON cp.id = cpf.customer_profile_id  
LEFT JOIN customer_analytics.purchase_history ph ON cp.id = ph.customer_profile_id
LEFT JOIN customer_analytics.expertise_indicators ei ON cp.id = ei.customer_profile_id
GROUP BY cp.id, cp.tenant_id, cp.visit_count, cp.total_purchase_amount, 
         cp.first_seen_at, cp.last_seen_at, cpf.expertise_level, cpf.preferred_categories,
         cpf.preferred_brands, cpf.average_purchase_amount, cpf.variety_seeking_score,
         cpf.recommendation_acceptance_rate, ei.expertise_score, ei.uses_strain_names,
         ei.uses_terpene_terminology;

COMMIT;