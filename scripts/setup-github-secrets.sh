#!/bin/bash

################################################################################
# GitHub Secrets Setup Script
#
# This script helps you configure all GitHub Actions secrets for the
# triple-environment deployment strategy.
#
# Usage:
#   chmod +x scripts/setup-github-secrets.sh
#   ./scripts/setup-github-secrets.sh
#
# Prerequisites:
#   - GitHub CLI installed: brew install gh
#   - Authenticated: gh auth login
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  GitHub Secrets Setup for Multi-Environment Deploy    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Install it with: brew install gh"
    echo "Or visit: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Not authenticated with GitHub CLI. Authenticating now...${NC}"
    gh auth login
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo -e "${GREEN}✓ Detected repository: $REPO${NC}"
echo ""

# Function to add a secret
add_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3

    if [ -z "$secret_value" ]; then
        echo -e "${YELLOW}⚠ Skipping $secret_name (empty value)${NC}"
        return
    fi

    echo -e "${BLUE}Setting: $secret_name${NC}"
    echo "$secret_value" | gh secret set "$secret_name" --repo="$REPO"
    echo -e "${GREEN}✓ Set $secret_name${NC}"
    echo ""
}

# Function to prompt for secret
prompt_for_secret() {
    local var_name=$1
    local prompt_text=$2
    local is_required=$3

    echo -e "${YELLOW}$prompt_text${NC}"

    if [ "$is_required" = "required" ]; then
        read -p "> " value
        while [ -z "$value" ]; do
            echo -e "${RED}This secret is required. Please enter a value.${NC}"
            read -p "> " value
        done
    else
        read -p "> (Optional, press Enter to skip) " value
    fi

    eval "$var_name='$value'"
}

################################################################################
# UAT ENVIRONMENT SECRETS
################################################################################

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  UAT Environment (Cloudflare + Koyeb + Neon)${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

prompt_for_secret CLOUDFLARE_API_TOKEN "Cloudflare API Token (from dashboard.cloudflare.com → My Profile → API Tokens):" "required"
prompt_for_secret CLOUDFLARE_ACCOUNT_ID "Cloudflare Account ID (from R2 or Pages dashboard):" "required"
prompt_for_secret KOYEB_TOKEN "Koyeb API Token (from app.koyeb.com → Organization Settings → API):" "required"
prompt_for_secret NEON_CONNECTION_STRING "Neon PostgreSQL connection string (from console.neon.tech):" "optional"
prompt_for_secret UPSTASH_REDIS_REST_URL "Upstash Redis REST URL:" "optional"
prompt_for_secret UPSTASH_REDIS_REST_TOKEN "Upstash Redis REST Token:" "optional"
prompt_for_secret R2_ACCESS_KEY_ID "Cloudflare R2 Access Key ID:" "optional"
prompt_for_secret R2_SECRET_ACCESS_KEY "Cloudflare R2 Secret Access Key:" "optional"

echo ""
echo -e "${GREEN}Adding UAT secrets to GitHub...${NC}"
add_secret "CLOUDFLARE_API_TOKEN" "$CLOUDFLARE_API_TOKEN" "Cloudflare API Token"
add_secret "CLOUDFLARE_ACCOUNT_ID" "$CLOUDFLARE_ACCOUNT_ID" "Cloudflare Account ID"
add_secret "KOYEB_TOKEN" "$KOYEB_TOKEN" "Koyeb API Token"
add_secret "NEON_CONNECTION_STRING" "$NEON_CONNECTION_STRING" "Neon DB Connection"
add_secret "UPSTASH_REDIS_REST_URL" "$UPSTASH_REDIS_REST_URL" "Upstash Redis URL"
add_secret "UPSTASH_REDIS_REST_TOKEN" "$UPSTASH_REDIS_REST_TOKEN" "Upstash Redis Token"
add_secret "R2_ACCESS_KEY_ID" "$R2_ACCESS_KEY_ID" "R2 Access Key"
add_secret "R2_SECRET_ACCESS_KEY" "$R2_SECRET_ACCESS_KEY" "R2 Secret Key"

################################################################################
# BETA ENVIRONMENT SECRETS
################################################################################

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  Beta Environment (Netlify + Render + Supabase)${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

prompt_for_secret NETLIFY_AUTH_TOKEN "Netlify Personal Access Token (from app.netlify.com/user/applications):" "required"
prompt_for_secret NETLIFY_SITE_ID_BETA_ADMIN "Netlify Site ID for Admin Dashboard (from site settings):" "optional"
prompt_for_secret NETLIFY_SITE_ID_BETA_COMMERCE "Netlify Site ID for Commerce (from site settings):" "optional"
prompt_for_secret RENDER_DEPLOY_HOOK_BETA "Render Deploy Hook URL (from dashboard.render.com → Service Settings → Deploy Hook):" "required"
prompt_for_secret SUPABASE_URL "Supabase Project URL (from app.supabase.com → Project Settings):" "optional"
prompt_for_secret SUPABASE_SERVICE_KEY "Supabase Service Role Key (from Project Settings → API):" "optional"

echo ""
echo -e "${GREEN}Adding Beta secrets to GitHub...${NC}"
add_secret "NETLIFY_AUTH_TOKEN" "$NETLIFY_AUTH_TOKEN" "Netlify Auth Token"
add_secret "NETLIFY_SITE_ID_BETA_ADMIN" "$NETLIFY_SITE_ID_BETA_ADMIN" "Netlify Site ID (Admin)"
add_secret "NETLIFY_SITE_ID_BETA_COMMERCE" "$NETLIFY_SITE_ID_BETA_COMMERCE" "Netlify Site ID (Commerce)"
add_secret "RENDER_DEPLOY_HOOK_BETA" "$RENDER_DEPLOY_HOOK_BETA" "Render Deploy Hook"
add_secret "SUPABASE_URL" "$SUPABASE_URL" "Supabase URL"
add_secret "SUPABASE_SERVICE_KEY" "$SUPABASE_SERVICE_KEY" "Supabase Service Key"

################################################################################
# PRE-PROD ENVIRONMENT SECRETS
################################################################################

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  Pre-PROD Environment (Vercel + Railway)${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

prompt_for_secret VERCEL_TOKEN "Vercel Token (from vercel.com/account/tokens):" "required"
prompt_for_secret VERCEL_ORG_ID "Vercel Organization ID (from team settings):" "required"
prompt_for_secret RAILWAY_TOKEN "Railway API Token (from railway.app/account/tokens):" "required"

echo ""
echo -e "${GREEN}Adding Pre-PROD secrets to GitHub...${NC}"
add_secret "VERCEL_TOKEN" "$VERCEL_TOKEN" "Vercel Token"
add_secret "VERCEL_ORG_ID" "$VERCEL_ORG_ID" "Vercel Org ID"
add_secret "RAILWAY_TOKEN" "$RAILWAY_TOKEN" "Railway Token"

################################################################################
# SHARED SECRETS (All Environments)
################################################################################

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  Shared Secrets${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

prompt_for_secret JWT_SECRET_KEY "JWT Secret Key (generate with: openssl rand -base64 32):" "optional"
prompt_for_secret SENTRY_DSN "Sentry DSN (from sentry.io):" "optional"
prompt_for_secret STRIPE_PUBLISHABLE_KEY "Stripe Publishable Key (test mode):" "optional"

echo ""
echo -e "${GREEN}Adding shared secrets to GitHub...${NC}"
add_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY" "JWT Secret"
add_secret "SENTRY_DSN" "$SENTRY_DSN" "Sentry DSN"
add_secret "STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY" "Stripe Key"

################################################################################
# SUMMARY
################################################################################

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                Setup Complete! ✓                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Secrets configured for repository: $REPO${NC}"
echo ""
echo "You can view all secrets at:"
echo "https://github.com/$REPO/settings/secrets/actions"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update .env.uat, .env.beta, .env.preprod with actual values"
echo "2. Push to develop branch to trigger UAT deployment"
echo "3. Check GitHub Actions: gh run list"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}"
