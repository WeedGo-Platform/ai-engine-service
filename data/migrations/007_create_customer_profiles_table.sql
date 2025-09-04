-- Create Customer Profiles table for storing customer information
-- This allows persistent customer data across sessions

CREATE TABLE IF NOT EXISTS customer_profiles (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    birth_date DATE,
    preferences JSONB DEFAULT '{}'::jsonb,
    notes TEXT,
    tags TEXT[],
    
    -- Session tracking
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_sessions INTEGER DEFAULT 1,
    total_interactions INTEGER DEFAULT 0,
    
    -- Purchase history
    total_purchases DECIMAL(10,2) DEFAULT 0.00,
    purchase_count INTEGER DEFAULT 0,
    favorite_products JSONB DEFAULT '[]'::jsonb,
    favorite_categories TEXT[],
    
    -- Preferences
    preferred_strain_type VARCHAR(50),
    preferred_consumption_method VARCHAR(50),
    medical_card BOOLEAN DEFAULT false,
    
    -- Marketing
    email_opt_in BOOLEAN DEFAULT false,
    sms_opt_in BOOLEAN DEFAULT false,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'chat',
    
    -- Compliance
    age_verified BOOLEAN DEFAULT false,
    age_verified_at TIMESTAMP,
    verification_method VARCHAR(50)
);

-- Create indexes for fast lookups
CREATE INDEX idx_customer_profiles_customer_id ON customer_profiles(customer_id);
CREATE INDEX idx_customer_profiles_email ON customer_profiles(email);
CREATE INDEX idx_customer_profiles_phone ON customer_profiles(phone);
CREATE INDEX idx_customer_profiles_last_seen ON customer_profiles(last_seen DESC);

-- Session details table to track each customer session
CREATE TABLE IF NOT EXISTS customer_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    customer_profile_id INTEGER REFERENCES customer_profiles(id),
    
    -- Session info
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Interaction details
    message_count INTEGER DEFAULT 0,
    products_viewed TEXT[],
    products_added_to_cart TEXT[],
    
    -- Context
    budtender_personality VARCHAR(100),
    initial_intent VARCHAR(100),
    resolved_intent VARCHAR(100),
    
    -- Outcome
    conversion BOOLEAN DEFAULT false,
    order_id VARCHAR(100),
    order_value DECIMAL(10,2),
    
    -- Satisfaction
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    
    -- Metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    referrer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for session lookups
CREATE INDEX idx_customer_sessions_session_id ON customer_sessions(session_id);
CREATE INDEX idx_customer_sessions_customer_id ON customer_sessions(customer_id);
CREATE INDEX idx_customer_sessions_started_at ON customer_sessions(started_at DESC);

-- Function to extract customer info from chat messages
CREATE OR REPLACE FUNCTION extract_customer_info(message TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}'::jsonb;
    email_pattern TEXT := '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}';
    phone_pattern TEXT := '(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})';
    name_indicators TEXT[] := ARRAY['my name is', 'i am', 'i''m', 'call me', 'this is'];
    indicator TEXT;
    potential_name TEXT;
BEGIN
    -- Extract email
    IF message ~* email_pattern THEN
        result := result || jsonb_build_object('email', 
            (regexp_match(message, email_pattern, 'i'))[1]);
    END IF;
    
    -- Extract phone
    IF message ~* phone_pattern THEN
        result := result || jsonb_build_object('phone', 
            regexp_replace((regexp_match(message, phone_pattern))[0], '[^0-9+]', '', 'g'));
    END IF;
    
    -- Extract name (basic heuristic)
    FOREACH indicator IN ARRAY name_indicators
    LOOP
        IF position(lower(indicator) in lower(message)) > 0 THEN
            -- Extract the word(s) after the indicator
            potential_name := trim(split_part(
                substring(lower(message) from position(lower(indicator) in lower(message)) + length(indicator)),
                ' ', 1
            ));
            IF length(potential_name) > 1 THEN
                result := result || jsonb_build_object('name', initcap(potential_name));
                EXIT; -- Stop after first match
            END IF;
        END IF;
    END LOOP;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to update customer profile from extracted info
CREATE OR REPLACE FUNCTION update_customer_profile_from_chat(
    p_customer_id VARCHAR,
    p_session_id VARCHAR,
    p_message TEXT
)
RETURNS void AS $$
DECLARE
    extracted_info JSONB;
    profile_id INTEGER;
BEGIN
    -- Extract customer info from message
    extracted_info := extract_customer_info(p_message);
    
    -- If we found any info, update or create profile
    IF extracted_info != '{}'::jsonb THEN
        -- Get or create customer profile
        INSERT INTO customer_profiles (customer_id)
        VALUES (p_customer_id)
        ON CONFLICT (customer_id) DO NOTHING;
        
        -- Update profile with extracted info
        UPDATE customer_profiles
        SET 
            name = COALESCE((extracted_info->>'name')::varchar, name),
            email = COALESCE((extracted_info->>'email')::varchar, email),
            phone = COALESCE((extracted_info->>'phone')::varchar, phone),
            last_seen = CURRENT_TIMESTAMP,
            total_interactions = total_interactions + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = p_customer_id;
    END IF;
    
    -- Update session tracking
    UPDATE customer_sessions
    SET 
        message_count = message_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION update_customer_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customer_profiles_timestamp
BEFORE UPDATE ON customer_profiles
FOR EACH ROW EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER update_customer_sessions_timestamp
BEFORE UPDATE ON customer_sessions
FOR EACH ROW EXECUTE FUNCTION update_customer_timestamp();