#!/bin/bash
# Download Qwen 2.5 7B - the primary multilingual model

MODEL_DIR="../models/multilingual"
MODEL_FILE="qwen2.5-7b-instruct-q4_k_m.gguf"
MODEL_URL="https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"

echo "📥 Downloading Qwen 2.5 7B Instruct (4.5GB)..."
echo "This is the primary multilingual model supporting 29+ languages"
echo ""

cd "$(dirname "$0")"
mkdir -p "$MODEL_DIR"

# Use curl with resume capability
curl -L -C - -o "$MODEL_DIR/$MODEL_FILE" "$MODEL_URL" --progress-bar

if [ $? -eq 0 ]; then
    echo "✅ Successfully downloaded Qwen 2.5 7B"
    echo "📍 Location: $MODEL_DIR/$MODEL_FILE"
    
    # Verify it's a valid GGUF file
    if head -c 4 "$MODEL_DIR/$MODEL_FILE" | grep -q "GGUF"; then
        echo "✓ Valid GGUF format confirmed"
    else
        echo "⚠️ Warning: File may not be valid GGUF format"
    fi
else
    echo "❌ Download failed. Please try again."
    exit 1
fi