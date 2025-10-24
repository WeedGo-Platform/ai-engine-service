#!/bin/bash

################################################################################
# Health Check All Environments
#
# Quick health check script for all three environments.
#
# Usage:
#   ./scripts/health-check-all.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Multi-Environment Health Check                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Environments to check
declare -A ENVIRONMENTS
ENVIRONMENTS[UAT]="https://weedgo-uat.koyeb.app"
ENVIRONMENTS[Beta]="https://weedgo-beta.onrender.com"
ENVIRONMENTS[Pre-PROD]="https://weedgo-preprod.up.railway.app"

# Frontend URLs to check
declare -A FRONTENDS_UAT
FRONTENDS_UAT[Admin]="https://weedgo-uat-admin.pages.dev"
FRONTENDS_UAT[Commerce]="https://weedgo-uat-commerce.pages.dev"

declare -A FRONTENDS_BETA
FRONTENDS_BETA[Admin]="https://weedgo-beta-admin.netlify.app"
FRONTENDS_BETA[Commerce]="https://weedgo-beta-commerce.netlify.app"

declare -A FRONTENDS_PREPROD
FRONTENDS_PREPROD[Admin]="https://weedgo-preprod-admin.vercel.app"
FRONTENDS_PREPROD[Commerce]="https://weedgo-preprod-commerce.vercel.app"

# Function to check a URL
check_url() {
    local name=$1
    local url=$2
    local timeout=10

    if curl -f -s -m $timeout "$url" > /dev/null 2>&1; then
        # Get response time
        response_time=$(curl -o /dev/null -s -w '%{time_total}\n' -m $timeout "$url")
        response_time_ms=$(echo "$response_time * 1000" | bc | cut -d. -f1)

        echo -e "  ${GREEN}✓${NC} $name: ${GREEN}OK${NC} (${response_time_ms}ms)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name: ${RED}FAILED${NC}"
        return 1
    fi
}

# Check backends
echo -e "${YELLOW}Backend Services:${NC}"
echo ""

total_backends=0
healthy_backends=0

for env in "${!ENVIRONMENTS[@]}"; do
    url="${ENVIRONMENTS[$env]}/health"
    total_backends=$((total_backends + 1))

    if check_url "$env" "$url"; then
        healthy_backends=$((healthy_backends + 1))
    fi
done

echo ""

# Check frontends
echo -e "${YELLOW}Frontend Applications:${NC}"
echo ""

total_frontends=0
healthy_frontends=0

echo -e "${BLUE}UAT Frontends:${NC}"
for app in "${!FRONTENDS_UAT[@]}"; do
    url="${FRONTENDS_UAT[$app]}"
    total_frontends=$((total_frontends + 1))

    if check_url "$app" "$url"; then
        healthy_frontends=$((healthy_frontends + 1))
    fi
done

echo ""
echo -e "${BLUE}Beta Frontends:${NC}"
for app in "${!FRONTENDS_BETA[@]}"; do
    url="${FRONTENDS_BETA[$app]}"
    total_frontends=$((total_frontends + 1))

    if check_url "$app" "$url"; then
        healthy_frontends=$((healthy_frontends + 1))
    fi
done

echo ""
echo -e "${BLUE}Pre-PROD Frontends:${NC}"
for app in "${!FRONTENDS_PREPROD[@]}"; do
    url="${FRONTENDS_PREPROD[$app]}"
    total_frontends=$((total_frontends + 1))

    if check_url "$app" "$url"; then
        healthy_frontends=$((healthy_frontends + 1))
    fi
done

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  Summary                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "Backends:  ${GREEN}$healthy_backends${NC}/$total_backends healthy"
echo -e "Frontends: ${GREEN}$healthy_frontends${NC}/$total_frontends healthy"
echo ""

total_services=$((total_backends + total_frontends))
healthy_services=$((healthy_backends + healthy_frontends))

health_percentage=$(echo "scale=1; $healthy_services * 100 / $total_services" | bc)

if [ "$healthy_services" = "$total_services" ]; then
    echo -e "${GREEN}✓ All services are healthy! ($health_percentage%)${NC}"
    exit 0
elif [ "$healthy_services" -gt $((total_services / 2)) ]; then
    echo -e "${YELLOW}⚠ Some services are down ($health_percentage% healthy)${NC}"
    exit 1
else
    echo -e "${RED}✗ Critical: Most services are down ($health_percentage% healthy)${NC}"
    exit 2
fi
