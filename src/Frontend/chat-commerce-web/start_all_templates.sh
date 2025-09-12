#!/bin/bash

# Kill any existing vite processes on our ports
for port in {5173..5180}; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

# Wait for ports to be released
sleep 2

# Template to port mapping
echo "Starting all template dev servers..."
echo "=================================="

# Start each template on a different port
echo "Starting weedgo on port 5173..."
VITE_TEMPLATE=weedgo npm run dev -- --port 5173 &

echo "Starting pot-palace on port 5174..."
VITE_TEMPLATE=pot-palace npm run dev -- --port 5174 &

echo "Starting modern-minimal on port 5175..."
VITE_TEMPLATE=modern-minimal npm run dev -- --port 5175 &

echo "Starting vintage on port 5176..."
VITE_TEMPLATE=vintage npm run dev -- --port 5176 &

echo "Starting rasta-vibes on port 5177..."
VITE_TEMPLATE=rasta-vibes npm run dev -- --port 5177 &

echo "Starting dark-tech on port 5178..."
VITE_TEMPLATE=dark-tech npm run dev -- --port 5178 &

echo "Starting metal on port 5179..."
VITE_TEMPLATE=metal npm run dev -- --port 5179 &

echo "Starting dirty on port 5180..."
VITE_TEMPLATE=dirty npm run dev -- --port 5180 &

echo ""
echo "All templates started!"
echo "=================================="
echo "Access templates at:"
echo "  weedgo:         http://localhost:5173"
echo "  pot-palace:     http://localhost:5174"
echo "  modern-minimal: http://localhost:5175"
echo "  vintage:        http://localhost:5176"
echo "  rasta-vibes:    http://localhost:5177"
echo "  dark-tech:      http://localhost:5178"
echo "  metal:          http://localhost:5179"
echo "  dirty:          http://localhost:5180"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
wait