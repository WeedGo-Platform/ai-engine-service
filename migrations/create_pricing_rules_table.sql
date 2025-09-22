-- Create pricing_rules table for store-specific category pricing
-- This table allows stores to set custom markup percentages for different product categories

CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    sub_sub_category VARCHAR(100),
    markup_percentage DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique rules per category level per store
    CONSTRAINT unique_store_category_rule UNIQUE (
        store_id,
        category,
        sub_category,
        sub_sub_category
    )
);

-- Create indexes for performance
CREATE INDEX idx_pricing_rules_store ON pricing_rules(store_id);
CREATE INDEX idx_pricing_rules_category ON pricing_rules(store_id, category);
CREATE INDEX idx_pricing_rules_subcategory ON pricing_rules(store_id, category, sub_category);
CREATE INDEX idx_pricing_rules_subsubcategory ON pricing_rules(store_id, category, sub_category, sub_sub_category);

-- Add trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_pricing_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pricing_rules_updated_at
    BEFORE UPDATE ON pricing_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_pricing_rules_updated_at();

-- Add comment for documentation
COMMENT ON TABLE pricing_rules IS 'Store-specific pricing rules for product categories. Allows stores to set different markup percentages at category, subcategory, and sub-subcategory levels.';
COMMENT ON COLUMN pricing_rules.markup_percentage IS 'The markup percentage to apply to products in this category. Applied on top of the unit cost to calculate retail price.';