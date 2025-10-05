-- Create system_settings table for storing system-wide configuration
-- Follows the same pattern as store_settings table

CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique combination of category and key
    UNIQUE(category, key)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);

-- Create trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_system_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_updated_at();

-- Add comment to table
COMMENT ON TABLE system_settings IS 'System-wide configuration settings for AI engine, models, and other global settings';
COMMENT ON COLUMN system_settings.category IS 'Configuration category (e.g., ai_model, system, features)';
COMMENT ON COLUMN system_settings.key IS 'Setting key within the category';
COMMENT ON COLUMN system_settings.value IS 'JSONB value for flexible configuration storage';
