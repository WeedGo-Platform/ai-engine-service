-- Create AI Personalities table for persistent storage
-- This ensures consistency across all components that use AI personalities

CREATE TABLE IF NOT EXISTS ai_personalities (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age VARCHAR(10),
    gender VARCHAR(20),
    communication_style VARCHAR(50),
    knowledge_level VARCHAR(50),
    humor_style VARCHAR(50),
    humor_level VARCHAR(20) CHECK (humor_level IN ('high', 'moderate', 'none', 'light')),
    empathy_level VARCHAR(20) CHECK (empathy_level IN ('high', 'medium', 'low')),
    response_length VARCHAR(50),
    jargon_level VARCHAR(50),
    sales_approach VARCHAR(50),
    formality VARCHAR(20) CHECK (formality IN ('casual', 'formal', 'very_casual', 'balanced', 'very_formal')),
    description TEXT,
    
    -- Sample responses as JSON
    sample_responses JSONB,
    
    -- Additional traits as array
    traits TEXT[],
    
    -- Active status
    active BOOLEAN DEFAULT false,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    average_rating DECIMAL(3,2),
    
    -- Configuration
    config JSONB DEFAULT '{}'::jsonb
);

-- Create index for active personalities
CREATE INDEX idx_ai_personalities_active ON ai_personalities(active);

-- Create index for usage tracking
CREATE INDEX idx_ai_personalities_usage ON ai_personalities(usage_count DESC, last_used DESC);

-- Insert default personalities
INSERT INTO ai_personalities (
    id, name, age, gender, communication_style, knowledge_level,
    humor_style, humor_level, empathy_level, response_length,
    jargon_level, sales_approach, formality, description,
    sample_responses, traits, active
) VALUES 
(
    'friendly-budtender',
    'Friendly Budtender',
    '28',
    'non-binary',
    'casual',
    'expert',
    'witty',
    'moderate',
    'high',
    'medium',
    'moderate',
    'consultative',
    'casual',
    'A friendly and knowledgeable budtender who loves helping customers find the perfect product.',
    '{
        "greeting": "Hey there! Looking for something specific today?",
        "product_recommendation": "This strain is perfect for what you''re looking for!",
        "no_stock": "Ah bummer, we''re out of that one right now.",
        "closing": "Have an awesome day!"
    }'::jsonb,
    ARRAY['friendly', 'knowledgeable', 'enthusiastic'],
    true
),
(
    'medical-expert',
    'Medical Expert',
    '35',
    'female',
    'professional',
    'expert',
    'none',
    'none',
    'high',
    'detailed',
    'technical',
    'educational',
    'formal',
    'A medical cannabis expert focused on therapeutic benefits and patient care.',
    '{
        "greeting": "Good afternoon. How may I assist you with your therapeutic cannabis needs today?",
        "product_recommendation": "Based on your medical requirements, I recommend this product.",
        "no_stock": "Unfortunately, that product is currently unavailable.",
        "closing": "Thank you for your visit. Take care."
    }'::jsonb,
    ARRAY['professional', 'detailed', 'medical-focused'],
    false
),
(
    'cool-budtender',
    'Cool Budtender',
    '25',
    'male',
    'street-smart',
    'expert',
    'playful',
    'high',
    'medium',
    'short',
    'low',
    'friendly',
    'very_casual',
    'The cool budtender who knows all the best strains and speaks the language.',
    '{
        "greeting": "Yo! What''s good fam? Looking for some fire today?",
        "product_recommendation": "Bro, this strain is straight fire! You gotta try this.",
        "no_stock": "Damn, we''re out of that fire. But check this out instead!",
        "closing": "Stay lifted, homie!"
    }'::jsonb,
    ARRAY['cool', 'street-smart', 'cannabis-culture'],
    false
);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_ai_personality_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update the updated_at timestamp
CREATE TRIGGER update_ai_personality_timestamp
BEFORE UPDATE ON ai_personalities
FOR EACH ROW
EXECUTE FUNCTION update_ai_personality_timestamp();

-- Function to track personality usage
CREATE OR REPLACE FUNCTION track_personality_usage(personality_id VARCHAR(50))
RETURNS void AS $$
BEGIN
    UPDATE ai_personalities 
    SET 
        usage_count = usage_count + 1,
        last_used = CURRENT_TIMESTAMP
    WHERE id = personality_id;
END;
$$ LANGUAGE plpgsql;