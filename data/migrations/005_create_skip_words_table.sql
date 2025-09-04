-- Create Skip Words table for managing search filter words
-- These words are excluded from product searches to improve relevance

CREATE TABLE IF NOT EXISTS skip_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create index for active skip words
CREATE INDEX idx_skip_words_active ON skip_words(active);

-- Create index for word lookup
CREATE INDEX idx_skip_words_word ON skip_words(word);

-- Insert default skip words
INSERT INTO skip_words (word, category, description) VALUES 
-- Conversational words
('show', 'conversational', 'Common request verb'),
('me', 'conversational', 'Personal pronoun'),
('some', 'conversational', 'Quantity indicator'),
('i', 'conversational', 'Personal pronoun'),
('want', 'conversational', 'Desire verb'),
('need', 'conversational', 'Requirement verb'),
('looking', 'conversational', 'Search verb'),
('for', 'conversational', 'Preposition'),
('the', 'conversational', 'Article'),
('a', 'conversational', 'Article'),
('an', 'conversational', 'Article'),
-- Question words
('what', 'question', 'Question word'),
('do', 'question', 'Auxiliary verb'),
('you', 'question', 'Personal pronoun'),
('think', 'question', 'Opinion verb'),
('or', 'question', 'Conjunction'),
('and', 'question', 'Conjunction'),
-- Request words
('got', 'request', 'Possession verb'),
('any', 'request', 'Quantity word'),
('have', 'request', 'Possession verb'),
('gimme', 'request', 'Slang for give me'),
('give', 'request', 'Transfer verb'),
('can', 'request', 'Modal verb'),
('could', 'request', 'Modal verb'),
('would', 'request', 'Modal verb'),
('should', 'request', 'Modal verb'),
-- Polite words
('please', 'polite', 'Politeness marker'),
('thanks', 'polite', 'Gratitude expression'),
-- Action words
('help', 'action', 'Assistance verb'),
('find', 'action', 'Search verb'),
('search', 'action', 'Search verb'),
('get', 'action', 'Obtain verb'),
-- Greeting words
('hey', 'greeting', 'Informal greeting'),
('hi', 'greeting', 'Greeting'),
('hello', 'greeting', 'Greeting'),
-- Response words
('yeah', 'response', 'Affirmative'),
('yes', 'response', 'Affirmative'),
('no', 'response', 'Negative'),
('okay', 'response', 'Agreement'),
('ok', 'response', 'Agreement'),
('sure', 'response', 'Agreement'),
-- Generic words
('something', 'generic', 'Vague reference'),
('stuff', 'generic', 'Vague reference'),
('thing', 'generic', 'Vague reference'),
('things', 'generic', 'Vague reference'),
('good', 'generic', 'Quality descriptor'),
('best', 'generic', 'Superlative'),
('like', 'generic', 'Similarity/preference'),
('product', 'generic', 'Generic product reference'),
('products', 'generic', 'Generic product reference'),
('item', 'generic', 'Generic reference'),
('items', 'generic', 'Generic reference'),
('option', 'generic', 'Choice reference'),
('options', 'generic', 'Choice reference'),
('choice', 'generic', 'Selection reference'),
('choices', 'generic', 'Selection reference')
ON CONFLICT (word) DO NOTHING;

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_skip_word_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update the updated_at timestamp
CREATE TRIGGER update_skip_word_timestamp
BEFORE UPDATE ON skip_words
FOR EACH ROW
EXECUTE FUNCTION update_skip_word_timestamp();