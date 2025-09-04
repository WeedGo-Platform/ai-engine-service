-- Add avatar and emoji columns to ai_personalities table
ALTER TABLE ai_personalities 
ADD COLUMN IF NOT EXISTS avatar TEXT,
ADD COLUMN IF NOT EXISTS emoji VARCHAR(10);

-- Update the existing personalities with some default emojis
UPDATE ai_personalities 
SET emoji = '🧑‍🌾' 
WHERE name LIKE '%Friendly%' AND emoji IS NULL;

UPDATE ai_personalities 
SET emoji = '👩‍⚕️' 
WHERE name LIKE '%Medical%' AND emoji IS NULL;

UPDATE ai_personalities 
SET emoji = '🧑‍🎤' 
WHERE name LIKE '%Chill%' AND emoji IS NULL;