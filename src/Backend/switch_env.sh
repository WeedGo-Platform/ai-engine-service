#!/bin/bash
# ============================================================================
# Quick Environment Switcher
# ============================================================================
# Switches between environment configurations and validates
# Usage: ./switch_env.sh [local|test|uat|beta|prod]
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ENV=$1

# Show usage if no argument
if [ -z "$ENV" ]; then
    echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   WeedGo Backend - Environment Switcher          ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC} ./switch_env.sh [environment]"
    echo ""
    echo -e "${YELLOW}Available environments:${NC}"
    echo -e "  ${GREEN}local${NC}  - Local development (port 5024, 300*)"
    echo -e "  ${GREEN}test${NC}   - Testing environment (port 6024, 60**)"
    echo -e "  ${GREEN}uat${NC}    - User acceptance testing (Cloud Run)"
    echo -e "  ${GREEN}beta${NC}   - Beta releases (Cloud Run)"
    echo -e "  ${GREEN}prod${NC}   - Production (Cloud Run)"
    echo ""
    echo -e "${YELLOW}Example:${NC}"
    echo -e "  ./switch_env.sh test"
    echo ""
    exit 1
fi

ENV_FILE=".env.$ENV"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ Error: $ENV_FILE not found${NC}"
    echo ""
    echo -e "${YELLOW}Available environment files:${NC}"
    ls -1 .env.* 2>/dev/null | grep -v ".env.example" | sed 's/^/  /'
    echo ""
    exit 1
fi

# Show current environment (if .env exists)
if [ -f ".env" ]; then
    CURRENT_ENV=$(grep "^ENVIRONMENT=" .env | cut -d '=' -f2 | tr -d '"' || echo "unknown")
    echo -e "${BLUE}Current environment: ${CURRENT_ENV}${NC}"
fi

# Backup current .env (if exists)
if [ -f ".env" ]; then
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env "$BACKUP_FILE"
    echo -e "${YELLOW}✓ Backed up current .env to $BACKUP_FILE${NC}"
fi

# Switch environment
cp "$ENV_FILE" .env
echo -e "${GREEN}✓ Switched to $ENV environment${NC}"
echo ""

# Show key configuration
echo -e "${BLUE}Environment Configuration:${NC}"
echo -e "  Environment: $(grep "^ENVIRONMENT=" .env | cut -d '=' -f2)"
echo -e "  Port: $(grep "^PORT=" .env | cut -d '=' -f2 || grep "^V5_PORT=" .env | cut -d '=' -f2)"
echo -e "  Database: $(grep "^DB_HOST=" .env | cut -d '=' -f2):$(grep "^DB_PORT=" .env | cut -d '=' -f2)/$(grep "^DB_NAME=" .env | cut -d '=' -f2)"
echo ""

# Validate
echo -e "${BLUE}Running validation...${NC}"
echo ""

# Check if python-dotenv is installed
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo -e "${YELLOW}⚠ python-dotenv not installed${NC}"
    echo -e "${YELLOW}Install with: pip install python-dotenv${NC}"
    echo ""
    echo -e "${GREEN}✓ Environment switched (validation skipped)${NC}"
    exit 0
fi

# Run validation
if python3 validate_env.py; then
    echo ""
    echo -e "${GREEN}✓ Environment ready to use!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  ${YELLOW}Start server:${NC} python3 api_server.py"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠ Environment switched but validation failed${NC}"
    echo -e "${YELLOW}Review errors above and update .env as needed${NC}"
    echo ""
    exit 1
fi
