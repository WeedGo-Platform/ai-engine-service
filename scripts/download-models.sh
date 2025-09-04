#!/bin/bash

# Download script for multiple LLM models
echo "🚀 WeedGo Multi-Model Download System"
echo "======================================"
echo ""

# Create models directory if it doesn't exist
mkdir -p models

# Function to download a model
download_model() {
    local NAME=$1
    local URL=$2
    local FILENAME=$3
    local SIZE=$4
    
    echo "📥 Downloading $NAME ($SIZE)..."
    
    if [ -f "models/$FILENAME" ]; then
        echo "✅ $NAME already exists, skipping..."
    else
        echo "   Downloading from Hugging Face..."
        curl -L -o "models/$FILENAME" "$URL"
        echo "✅ $NAME downloaded successfully!"
    fi
    echo ""
}

# Menu for model selection
echo "Available Models for Download:"
echo "1. Llama 2 7B Chat (3.8GB) - General purpose, excellent reasoning"
echo "2. Mistral 7B Instruct (4.1GB) - Best for medical/technical queries"  
echo "3. CodeLlama 7B (3.8GB) - Technical documentation and API queries"
echo "4. Phi-2 (1.5GB) - Fast, lightweight for edge deployment"
echo "5. All models (recommended for production)"
echo ""
read -p "Select models to download (1-5): " choice

case $choice in
    1)
        download_model \
            "Llama 2 7B Chat" \
            "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf" \
            "llama-2-7b-chat.Q4_K_M.gguf" \
            "3.8GB"
        ;;
    2)
        download_model \
            "Mistral 7B Instruct v0.2" \
            "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf" \
            "mistral-7b-instruct-v0.2.Q4_K_M.gguf" \
            "4.1GB"
        ;;
    3)
        download_model \
            "CodeLlama 7B Instruct" \
            "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf" \
            "codellama-7b-instruct.Q4_K_M.gguf" \
            "3.8GB"
        ;;
    4)
        download_model \
            "Microsoft Phi-2" \
            "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf" \
            "phi-2.Q4_K_M.gguf" \
            "1.5GB"
        ;;
    5)
        echo "📦 Downloading all models for production deployment..."
        echo ""
        
        download_model \
            "Llama 2 7B Chat" \
            "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf" \
            "llama-2-7b-chat.Q4_K_M.gguf" \
            "3.8GB"
        
        download_model \
            "Mistral 7B Instruct v0.2" \
            "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf" \
            "mistral-7b-instruct-v0.2.Q4_K_M.gguf" \
            "4.1GB"
        
        download_model \
            "Microsoft Phi-2" \
            "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf" \
            "phi-2.Q4_K_M.gguf" \
            "1.5GB"
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac

echo "======================================"
echo "📊 Model Summary:"
ls -lh models/*.gguf 2>/dev/null || echo "No models downloaded yet"
echo ""
echo "✅ Setup complete! Models are ready for use."
echo ""
echo "🎯 Next steps:"
echo "1. Test models: python3 multi-model-budtender.py"
echo "2. Run A/B test: python3 multi-model-budtender.py ab"
echo "3. Start API: python3 multi-model-api.py"
echo ""