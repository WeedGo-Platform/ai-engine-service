#!/bin/bash

################################################################################
# Multi-Environment Deployment Helper
#
# Quickly deploy to any environment with validation and health checks.
#
# Usage:
#   ./scripts/deploy-environment.sh uat
#   ./scripts/deploy-environment.sh beta
#   ./scripts/deploy-environment.sh preprod
#   ./scripts/deploy-environment.sh all
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENV=$1

if [ -z "$ENV" ]; then
    echo -e "${RED}Error: Environment not specified${NC}"
    echo "Usage: $0 [uat|beta|preprod|all]"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Multi-Environment Deployment                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Deployment configuration
declare -A BRANCH_MAP
BRANCH_MAP[uat]="develop"
BRANCH_MAP[beta]="staging"
BRANCH_MAP[preprod]="release"

declare -A BACKEND_URL
BACKEND_URL[uat]="https://weedgo-uat.koyeb.app"
BACKEND_URL[beta]="https://weedgo-beta.onrender.com"
BACKEND_URL[preprod]="https://weedgo-preprod.up.railway.app"

# Function to deploy a single environment
deploy_env() {
    local env=$1
    local branch=${BRANCH_MAP[$env]}

    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}  Deploying to $env (branch: $branch)${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo ""

    # Check if we're on the correct branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$branch" ]; then
        echo -e "${BLUE}Switching to branch: $branch${NC}"
        git checkout $branch
    fi

    # Pull latest changes
    echo -e "${BLUE}Pulling latest changes...${NC}"
    git pull origin $branch

    # Push to trigger deployment
    echo -e "${BLUE}Pushing to trigger deployment...${NC}"
    git push origin $branch

    echo -e "${GREEN}✓ Deployment triggered for $env${NC}"
    echo ""

    # Wait for deployment
    echo -e "${YELLOW}Waiting for deployment to complete (60 seconds)...${NC}"
    sleep 60

    # Health check
    echo -e "${BLUE}Running health check...${NC}"
    if health_check "$env"; then
        echo -e "${GREEN}✓ $env deployment successful!${NC}"
    else
        echo -e "${RED}✗ $env deployment health check failed${NC}"
        return 1
    fi

    echo ""
}

# Function to check health
health_check() {
    local env=$1
    local url="${BACKEND_URL[$env]}/health"
    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo -e "${BLUE}Health check attempt $attempt/$max_attempts: $url${NC}"

        if curl -f -s "$url" > /dev/null 2>&1; then
            response=$(curl -s "$url")
            echo -e "${GREEN}Response: $response${NC}"
            return 0
        fi

        echo -e "${YELLOW}Waiting 10 seconds before retry...${NC}"
        sleep 10
        ((attempt++))
    done

    return 1
}

# Main deployment logic
if [ "$ENV" = "all" ]; then
    echo -e "${YELLOW}Deploying to all environments...${NC}"
    echo ""

    deploy_env "uat"
    deploy_env "beta"
    deploy_env "preprod"

    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      All Deployments Complete! ✓                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
else
    if [ -z "${BRANCH_MAP[$ENV]}" ]; then
        echo -e "${RED}Error: Invalid environment '$ENV'${NC}"
        echo "Valid environments: uat, beta, preprod, all"
        exit 1
    fi

    deploy_env "$ENV"

    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Deployment Complete! ✓                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo -e "${BLUE}View deployments:${NC}"
echo "  UAT:      ${BACKEND_URL[uat]}"
echo "  Beta:     ${BACKEND_URL[beta]}"
echo "  Pre-PROD: ${BACKEND_URL[preprod]}"
echo ""
echo -e "${BLUE}Check GitHub Actions:${NC}"
echo "  gh run list"
echo "  gh run watch"
echo ""
