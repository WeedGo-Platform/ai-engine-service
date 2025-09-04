-- Create training_examples table to persist AI training data
CREATE TABLE IF NOT EXISTS training_examples (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    expected_intent VARCHAR(100) NOT NULL,
    expected_response TEXT,
    entities JSONB DEFAULT '{}',
    expected_products JSONB DEFAULT '[]',
    expected_response_qualities JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    feedback_score FLOAT DEFAULT 0.5,
    dataset_id VARCHAR(255),
    dataset_name VARCHAR(255),
    added_by VARCHAR(100) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_training_examples_intent ON training_examples(expected_intent);
CREATE INDEX IF NOT EXISTS idx_training_examples_dataset ON training_examples(dataset_id);
CREATE INDEX IF NOT EXISTS idx_training_examples_created ON training_examples(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_examples_active ON training_examples(is_active);

-- Create training_sessions table to track training history
CREATE TABLE IF NOT EXISTS training_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    examples_trained INTEGER DEFAULT 0,
    accuracy_before FLOAT DEFAULT 0,
    accuracy_after FLOAT DEFAULT 0,
    improvements JSONB DEFAULT '{}',
    dataset_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'in_progress',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create index for session queries
CREATE INDEX IF NOT EXISTS idx_training_sessions_status ON training_sessions(status);
CREATE INDEX IF NOT EXISTS idx_training_sessions_started ON training_sessions(started_at DESC);

-- Insert some default training examples to get started
INSERT INTO training_examples (query, expected_intent, expected_response, entities, dataset_id, dataset_name) VALUES
-- Cannabis slang and terminology
('got any fire?', 'product_search', 'I''ll help you find our highest quality cannabis products!', '{"quality": "premium", "slang": "fire"}', 'cannabis_slang_v1', 'Cannabis Slang & Terminology'),
('gimme a zip', 'product_search', 'I''ll help you find products available in ounce (28g) quantities.', '{"quantity": "28g", "slang": "zip"}', 'cannabis_slang_v1', 'Cannabis Slang & Terminology'),
('looking for some gas', 'product_search', 'I''ll find products with diesel or fuel-like terpene profiles for you.', '{"terpene_profile": "diesel", "slang": "gas"}', 'cannabis_slang_v1', 'Cannabis Slang & Terminology'),
('need some loud', 'product_search', 'I''ll show you our most potent and aromatic strains.', '{"quality": "potent", "slang": "loud"}', 'cannabis_slang_v1', 'Cannabis Slang & Terminology'),
('got any mids?', 'product_search', 'I''ll find our mid-tier products that offer good value.', '{"quality": "mid-tier", "slang": "mids"}', 'cannabis_slang_v1', 'Cannabis Slang & Terminology'),

-- Medical conditions and effects
('what helps with anxiety?', 'medical_recommendation', 'I''ll find products known for their calming and anxiety-reducing effects.', '{"condition": "anxiety", "effect": "calming"}', 'medical_conditions_v1', 'Medical Conditions & Effects'),
('I have chronic pain', 'medical_recommendation', 'I''ll show you products that may help with pain management.', '{"condition": "chronic_pain", "effect": "pain_relief"}', 'medical_conditions_v1', 'Medical Conditions & Effects'),
('need something for insomnia', 'medical_recommendation', 'I''ll find products with sedating effects that may help with sleep.', '{"condition": "insomnia", "effect": "sedating"}', 'medical_conditions_v1', 'Medical Conditions & Effects'),
('dealing with nausea', 'medical_recommendation', 'I''ll find products that may help with nausea relief.', '{"condition": "nausea", "effect": "anti_nausea"}', 'medical_conditions_v1', 'Medical Conditions & Effects'),
('help with appetite', 'medical_recommendation', 'I''ll show you products known for stimulating appetite.', '{"condition": "appetite_loss", "effect": "appetite_stimulant"}', 'medical_conditions_v1', 'Medical Conditions & Effects'),

-- Product quantities and sizes
('half ounce of pink kush', 'product_search', 'I''ll find Pink Kush available in 14g quantities.', '{"quantity": "14g", "strain": "pink_kush"}', 'product_quantities_v1', 'Product Quantities & Sizes'),
('eighth of something fruity', 'product_search', 'I''ll find fruity strains available in 3.5g quantities.', '{"quantity": "3.5g", "flavor": "fruity"}', 'product_quantities_v1', 'Product Quantities & Sizes'),
('quarter of your best indica', 'product_search', 'I''ll show you our premium indica strains in 7g quantities.', '{"quantity": "7g", "strain_type": "indica", "quality": "premium"}', 'product_quantities_v1', 'Product Quantities & Sizes'),
('gram of shatter', 'product_search', 'I''ll find shatter concentrates available by the gram.', '{"quantity": "1g", "product_type": "concentrate", "concentrate_type": "shatter"}', 'product_quantities_v1', 'Product Quantities & Sizes'),
('dime bag', 'product_search', 'I''ll find products available in small quantities.', '{"quantity": "small", "slang": "dime_bag"}', 'product_quantities_v1', 'Product Quantities & Sizes'),

-- Specific product searches
('kush cookies', 'product_search', 'I''ll find Kush Cookies products for you.', '{"strain": "kush_cookies"}', 'product_search_v1', 'Product Searches'),
('island kush', 'product_search', 'I''ll find Island Kush products for you.', '{"strain": "island_kush"}', 'product_search_v1', 'Product Searches'),
('pink kush', 'product_search', 'I''ll find Pink Kush products for you.', '{"strain": "pink_kush"}', 'product_search_v1', 'Product Searches'),
('blue dream', 'product_search', 'I''ll find Blue Dream products for you.', '{"strain": "blue_dream"}', 'product_search_v1', 'Product Searches'),
('og kush', 'product_search', 'I''ll find OG Kush products for you.', '{"strain": "og_kush"}', 'product_search_v1', 'Product Searches');

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_training_examples_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update the updated_at column
CREATE TRIGGER training_examples_updated_at_trigger
BEFORE UPDATE ON training_examples
FOR EACH ROW
EXECUTE FUNCTION update_training_examples_updated_at();

-- Add comment to table
COMMENT ON TABLE training_examples IS 'Stores AI training examples for continuous learning and improvement';
COMMENT ON TABLE training_sessions IS 'Tracks AI training sessions and their performance metrics';