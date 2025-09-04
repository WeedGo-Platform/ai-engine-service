#!/bin/bash

# Setup script for offline multilingual AI system
# Supports: English, Spanish, French, Portuguese, Chinese, Arabic

echo "=========================================="
echo "Offline Multilingual AI Setup"
echo "=========================================="

# Create directory structure
echo "Creating directory structure..."
mkdir -p models/gguf
mkdir -p models/lora_adapters
mkdir -p models/tokenizers
mkdir -p models/embeddings
mkdir -p cache/semantic
mkdir -p cache/translations
mkdir -p data/terminology

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q llama-cpp-python==0.2.90
pip install -q fasttext
pip install -q sentence-transformers
pip install -q tokenizers
pip install -q numpy scipy
pip install -q langdetect lingua-language-detector
pip install -q chromadb
pip install -q onnxruntime

# Download llama.cpp
echo "Setting up llama.cpp..."
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
    make LLAMA_METAL=1  # For Mac Metal acceleration
    # make LLAMA_CUDA=1  # For NVIDIA GPUs
    cd ..
fi

# Download language detection model
echo "Downloading offline language detection model..."
if [ ! -f "models/lid.176.bin" ]; then
    wget -P models/ https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
fi

# Download embedding model for semantic cache
echo "Downloading embedding models..."
python -c "
from sentence_transformers import SentenceTransformer
import os

# Download multilingual embedding model
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
model.save('models/embeddings/multilingual-minilm')

# Download medical embedding model
model = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')
model.save('models/embeddings/medical-bert')

print('Embedding models downloaded successfully')
"

# Download Qwen model (using smaller version for testing)
echo "Downloading Qwen model..."
echo "NOTE: For production, download Qwen-14B-Chat-GGUF from:"
echo "https://huggingface.co/Qwen/Qwen-14B-Chat-GGUF"
echo ""
echo "For testing, we'll use a smaller model:"

# Download a smaller test model (Qwen-1.8B for testing)
if [ ! -f "models/gguf/qwen-1_8b-chat-q4_k_m.gguf" ]; then
    echo "Downloading Qwen-1.8B test model..."
    wget -P models/gguf/ https://huggingface.co/Qwen/Qwen-1_8B-Chat-GGUF/resolve/main/qwen-1_8b-chat-q4_k_m.gguf
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Download production model: Qwen-14B-Chat-GGUF"
echo "2. Place in: models/gguf/"
echo "3. Run: python test_offline_multilingual.py"
echo ""