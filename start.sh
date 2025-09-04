#!/bin/bash

# WeedGo AI Engine Service Startup Script
# Production-ready API with multi-model support

echo "🚀 Starting WeedGo AI Engine Service..."
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✓ Python version: $python_version"

# Check if models exist
if [ -d "models" ]; then
    echo "✓ Models directory found"
    
    if [ -f "models/llama-2-7b-chat.Q4_K_M.gguf" ]; then
        echo "  ✓ Llama 2 model installed"
    else
        echo "  ⚠ Llama 2 model not found - run: python3 scripts/download-models.sh"
    fi
    
    if [ -f "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf" ]; then
        echo "  ✓ Mistral model installed"
    else
        echo "  ⚠ Mistral model not found (optional) - run: python3 scripts/download-mistral.py"
    fi
else
    echo "❌ Models directory not found"
    echo "   Creating models directory..."
    mkdir -p models
fi

# Check environment
if [ -f ".env" ]; then
    echo "✓ Environment configuration found"
    source .env
else
    echo "⚠ No .env file found - using defaults"
fi

# Set default values if not in env
export AI_ENGINE_HOST=${AI_ENGINE_HOST:-"0.0.0.0"}
export AI_ENGINE_PORT=${AI_ENGINE_PORT:-8000}
export ENVIRONMENT=${ENVIRONMENT:-"development"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

echo ""
echo "Configuration:"
echo "  Host: $AI_ENGINE_HOST"
echo "  Port: $AI_ENGINE_PORT"
echo "  Environment: $ENVIRONMENT"
echo "  Log Level: $LOG_LEVEL"
echo ""

# Kill any existing process on the port
if lsof -Pi :$AI_ENGINE_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠ Port $AI_ENGINE_PORT is in use, stopping existing process..."
    lsof -Pi :$AI_ENGINE_PORT -sTCP:LISTEN -t | xargs kill -9
    sleep 1
fi

# Start the service
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting in PRODUCTION mode..."
    echo "=========================================="
    
    # Use gunicorn with uvicorn workers for production
    gunicorn api.main:app \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind $AI_ENGINE_HOST:$AI_ENGINE_PORT \
        --log-level $LOG_LEVEL \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --daemon
    
    echo "✅ Service started in background (daemon mode)"
    echo "   Logs: logs/access.log and logs/error.log"
    echo "   API Docs: http://localhost:$AI_ENGINE_PORT/api/docs"
    
else
    echo "🔧 Starting in DEVELOPMENT mode..."
    echo "=========================================="
    
    # Use uvicorn directly for development with auto-reload
    python3 -m uvicorn api.main:app \
        --host $AI_ENGINE_HOST \
        --port $AI_ENGINE_PORT \
        --reload \
        --log-level $LOG_LEVEL
fi