-- Voice Authentication System Tables
-- Migration: voice_auth_tables.sql

-- Voice profiles table for storing voice biometric data
CREATE TABLE IF NOT EXISTS voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    voice_embedding TEXT NOT NULL, -- Base64 encoded voice features
    age_verification JSONB DEFAULT '{}', -- Age verification results
    metadata JSONB DEFAULT '{}', -- Additional metadata (sample rate, feature dim, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Voice authentication logs for auditing
CREATE TABLE IF NOT EXISTS voice_auth_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    success BOOLEAN NOT NULL,
    confidence_score DECIMAL(5,3), -- 0.000 to 1.000
    age_info JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Age verification logs for compliance
CREATE TABLE IF NOT EXISTS age_verification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    age_info JSONB NOT NULL,
    verified BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    session_id VARCHAR(255)
);

-- Users table (ensure it exists with required fields)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    phone VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    age_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user',
    active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_voice_profiles_user_id ON voice_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_auth_logs_user_id ON voice_auth_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_auth_logs_timestamp ON voice_auth_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_age_verification_logs_timestamp ON age_verification_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active);

-- Add foreign key constraints
ALTER TABLE voice_profiles 
ADD CONSTRAINT fk_voice_profiles_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE voice_auth_logs 
ADD CONSTRAINT fk_voice_auth_logs_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;