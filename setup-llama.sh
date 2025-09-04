#!/bin/bash

# Setup script for Llama 2 7B model
echo "🚀 Setting up Llama 2 7B for WeedGo AI Budtender"
echo "================================================"

# Create models directory
mkdir -p models

# Download quantized Llama 2 7B Chat model (4-bit quantization, ~4GB)
echo "📥 Downloading Llama 2 7B Chat model (Q4_K_M quantization)..."
echo "This is a 4GB download, please be patient..."

# Using TheBloke's quantized version for efficiency
if [ ! -f "models/llama-2-7b-chat.Q4_K_M.gguf" ]; then
    curl -L -o models/llama-2-7b-chat.Q4_K_M.gguf \
        "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
    echo "✅ Model downloaded successfully!"
else
    echo "✅ Model already exists, skipping download"
fi

echo ""
echo "📊 Model Information:"
echo "- Model: Llama 2 7B Chat"
echo "- Quantization: Q4_K_M (4-bit)"
echo "- Size: ~4GB"
echo "- Performance: Runs on CPU, better with GPU"
echo "- Memory Required: ~6GB RAM"
echo ""
echo "✅ Setup complete! Ready to use Llama 2 7B"