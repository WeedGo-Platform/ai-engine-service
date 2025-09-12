#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Shutting down all template servers...${NC}"
    jobs -p | xargs kill 2>/dev/null
    exit 0
}

# Set up trap for clean exit
trap cleanup SIGINT SIGTERM EXIT

# Clear screen
clear

echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🚀 WeedGo Multi-Template Development Server     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Kill any existing processes on our ports
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
for port in {5173..5180}; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

# Wait for ports to be freed
sleep 1

# Start all templates
echo -e "${CYAN}Starting all template servers...${NC}"
echo ""

# Function to start a template
start_template() {
    local name=$1
    local port=$2
    local color=$3
    
    echo -e "${color}[${name}:${port}]${NC} Starting..."
    VITE_TEMPLATE=$name npm run dev -- --port $port 2>&1 | sed "s/^/[$name:$port] /" &
}

# Start each template with a different color prefix
start_template "weedgo" 5173 "$GREEN"
start_template "pot-palace" 5174 "$MAGENTA"
start_template "modern-minimal" 5175 "$CYAN"
start_template "vintage" 5176 "$YELLOW"
start_template "rasta-vibes" 5177 "$RED"
start_template "dark-tech" 5178 "$BLUE"
start_template "metal" 5179 "$WHITE"
start_template "dirty" 5180 "$GREEN"

# Wait a moment for servers to start
sleep 3

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           All template servers running!              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Access your templates at:${NC}"
echo -e "  ${GREEN}weedgo${NC}         → http://localhost:5173"
echo -e "  ${MAGENTA}pot-palace${NC}     → http://localhost:5174"
echo -e "  ${CYAN}modern-minimal${NC} → http://localhost:5175"
echo -e "  ${YELLOW}vintage${NC}        → http://localhost:5176"
echo -e "  ${RED}rasta-vibes${NC}    → http://localhost:5177"
echo -e "  ${BLUE}dark-tech${NC}      → http://localhost:5178"
echo -e "  ${WHITE}metal${NC}          → http://localhost:5179"
echo -e "  ${GREEN}dirty${NC}          → http://localhost:5180"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Keep script running
wait