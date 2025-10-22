-- Migration: Create OCR Scan History Table
-- Description: Stores history of OCR extractions from accessory images
-- Date: 2025-10-22

-- Create OCR scan history table
CREATE TABLE IF NOT EXISTS ocr_scan_history (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    image_url TEXT,
    extracted_text TEXT,
    extracted_data JSONB,
    barcode VARCHAR(50),
    confidence_score DECIMAL(5,4), -- Changed to allow values like 0.9999
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'success', 'low_confidence', 'failed', 'pending'
    provider VARCHAR(100), -- OCR provider used (e.g., 'ollama_qwen3:4b', 'paddleocr-vl')
    processed_by VARCHAR(100), -- User or system that initiated the scan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on store_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_ocr_scan_history_store_id ON ocr_scan_history(store_id);

-- Create index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_ocr_scan_history_created_at ON ocr_scan_history(created_at DESC);

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_ocr_scan_history_status ON ocr_scan_history(status);

-- Create index on provider for analytics
CREATE INDEX IF NOT EXISTS idx_ocr_scan_history_provider ON ocr_scan_history(provider);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_ocr_scan_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ocr_scan_history_updated_at_trigger
BEFORE UPDATE ON ocr_scan_history
FOR EACH ROW
EXECUTE FUNCTION update_ocr_scan_history_updated_at();

-- Add comments for documentation
COMMENT ON TABLE ocr_scan_history IS 'Stores history of OCR extractions from product images';
COMMENT ON COLUMN ocr_scan_history.store_id IS 'Store that performed the OCR scan';
COMMENT ON COLUMN ocr_scan_history.extracted_text IS 'Raw text extracted from image';
COMMENT ON COLUMN ocr_scan_history.extracted_data IS 'Structured JSON data extracted (product name, brand, etc.)';
COMMENT ON COLUMN ocr_scan_history.confidence_score IS 'Overall confidence score (0.0 to 1.0)';
COMMENT ON COLUMN ocr_scan_history.status IS 'Scan status: success, low_confidence, failed, pending';
COMMENT ON COLUMN ocr_scan_history.provider IS 'AI provider used for OCR (e.g., ollama_qwen3:4b, paddleocr-vl)';
