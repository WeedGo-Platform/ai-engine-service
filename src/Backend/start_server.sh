#!/bin/bash

# WeedGo AI Engine - Main Server Startup Script
# This script starts the combined server with both WeedGo API and AGI services

echo "🚀 Starting WeedGo AI Engine Server..."
echo "   This server includes:"
echo "   ✅ WeedGo API endpoints (stores, products, cart, etc.)"
echo "   ✅ AGI Dashboard and AI services"
echo "   ✅ WebSocket support for chat and voice"
echo ""

# Check if already running
if lsof -i :5024 > /dev/null 2>&1; then
    echo "⚠️  Warning: Port 5024 is already in use!"
    echo "   Running process:"
    lsof -i :5024 | grep LISTEN
    echo ""
    read -p "Kill existing process and restart? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -t -i :5024)
        kill $PID
        echo "✅ Killed process $PID"
        sleep 2
    else
        echo "❌ Exiting without starting new server"
        exit 1
    fi
fi

# Start the server
echo "Starting server on port 5024..."
python3 api_server.py

# Note: For background operation, use:
# nohup python3 api_server.py > server.log 2>&1 &