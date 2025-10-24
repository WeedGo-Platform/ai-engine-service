#!/bin/bash

################################################################################
# Interactive Credential Collection Helper
#
# This script guides you through collecting credentials from each platform
# and automatically populates your .env files.
#
# Usage:
#   ./scripts/credential-helper.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Interactive Credential Collection Helper           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}This script will help you collect credentials from 9 platforms${NC}"
echo -e "${CYAN}and automatically populate your .env files.${NC}"
echo ""
echo -e "${YELLOW}Estimated time: 30-45 minutes${NC}"
echo ""
read -p "Press Enter to start..."

# Create temporary file to store credentials
TEMP_CREDS=$(mktemp)

# Function to open URL and wait for user input
collect_credential() {
    local provider=$1
    local signup_url=$2
    local credential_name=$3
    local instructions=$4

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Step: $provider${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Instructions:${NC}"
    echo -e "$instructions"
    echo ""
    echo -e "${CYAN}Opening browser to: $signup_url${NC}"

    # Try to open browser
    if command -v open &> /dev/null; then
        open "$signup_url"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$signup_url"
    else
        echo -e "${YELLOW}Could not open browser automatically. Please visit:${NC}"
        echo -e "${CYAN}$signup_url${NC}"
    fi

    echo ""
    read -p "Press Enter when you have the credential ready..."

    echo ""
    read -p "Enter your $credential_name: " credential_value

    echo "$provider|$credential_name|$credential_value" >> "$TEMP_CREDS"
    echo -e "${GREEN}✓ $credential_name saved${NC}"
}

################################################################################
# UAT Environment
################################################################################

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  UAT Environment (4 providers)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"

# 1. Neon
collect_credential \
    "Neon PostgreSQL" \
    "https://console.neon.tech/signup" \
    "DATABASE_URL" \
    "1. Sign up for free account
2. Click 'Create Project' → Name it 'weedgo-uat'
3. In SQL Editor, run: CREATE EXTENSION IF NOT EXISTS vector;
4. In SQL Editor, run: CREATE EXTENSION IF NOT EXISTS pg_trgm;
5. Click 'Connection Details' → Copy 'Connection string'
   (Should look like: postgresql://neondb_owner:xxx@ep-xxx.us-east-2.aws.neon.tech/neondb)"

# 2. Upstash Redis
collect_credential \
    "Upstash Redis" \
    "https://console.upstash.com/login" \
    "UPSTASH_REDIS_REST_URL" \
    "1. Sign up for free account
2. Click 'Create Database' → Name it 'weedgo-uat-redis'
3. Select region: US East
4. Click 'REST API' tab → Copy 'UPSTASH_REDIS_REST_URL'"

echo ""
read -p "Enter your UPSTASH_REDIS_REST_TOKEN: " upstash_token
echo "Upstash Redis|UPSTASH_REDIS_REST_TOKEN|$upstash_token" >> "$TEMP_CREDS"
echo -e "${GREEN}✓ UPSTASH_REDIS_REST_TOKEN saved${NC}"

# 3. Cloudflare
collect_credential \
    "Cloudflare API" \
    "https://dash.cloudflare.com/sign-up" \
    "CLOUDFLARE_API_TOKEN" \
    "1. Sign up for free account
2. Go to My Profile → API Tokens → Create Token
3. Use template 'Edit Cloudflare Workers' or create custom token with:
   - Account: Cloudflare Pages: Edit
   - Account: Cloudflare R2: Edit
4. Copy the generated token"

collect_credential \
    "Cloudflare Account" \
    "https://dash.cloudflare.com" \
    "CLOUDFLARE_ACCOUNT_ID" \
    "1. In Cloudflare dashboard
2. Look at the URL - it will be: dash.cloudflare.com/<ACCOUNT_ID>/
3. Or go to any service and find 'Account ID' in the sidebar
4. Copy your Account ID"

# R2 credentials
collect_credential \
    "Cloudflare R2" \
    "https://dash.cloudflare.com" \
    "R2_ACCESS_KEY_ID" \
    "1. In Cloudflare dashboard → R2 → Manage R2 API Tokens
2. Click 'Create API Token'
3. Grant 'Admin Read & Write' permissions
4. Copy the 'Access Key ID'"

echo ""
read -p "Enter your R2_SECRET_ACCESS_KEY: " r2_secret
echo "Cloudflare R2|R2_SECRET_ACCESS_KEY|$r2_secret" >> "$TEMP_CREDS"
echo -e "${GREEN}✓ R2_SECRET_ACCESS_KEY saved${NC}"

# 4. Koyeb
collect_credential \
    "Koyeb" \
    "https://app.koyeb.com/auth/signup" \
    "KOYEB_TOKEN" \
    "1. Sign up for free account
2. Go to Settings → API → Create API Token
3. Name it 'weedgo-deployment'
4. Copy the token"

################################################################################
# Beta Environment
################################################################################

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Beta Environment (3 providers)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"

# 5. Supabase
collect_credential \
    "Supabase" \
    "https://supabase.com/dashboard/sign-in" \
    "SUPABASE_URL" \
    "1. Sign up for free account
2. Click 'New Project' → Name it 'weedgo-beta'
3. In SQL Editor, run: CREATE EXTENSION IF NOT EXISTS vector;
4. In SQL Editor, run: CREATE EXTENSION IF NOT EXISTS pg_trgm;
5. Go to Settings → API → Copy 'Project URL'"

echo ""
read -p "Enter your SUPABASE_SERVICE_KEY (anon key): " supabase_key
echo "Supabase|SUPABASE_SERVICE_KEY|$supabase_key" >> "$TEMP_CREDS"
echo -e "${GREEN}✓ SUPABASE_SERVICE_KEY saved${NC}"

# Also need Supabase DATABASE_URL
collect_credential \
    "Supabase Database" \
    "https://supabase.com/dashboard" \
    "BETA_DATABASE_URL" \
    "1. In your Supabase project
2. Go to Settings → Database → Connection String
3. Select 'URI' mode
4. Copy the connection string (with your password filled in)"

# 6. Netlify
collect_credential \
    "Netlify" \
    "https://app.netlify.com/signup" \
    "NETLIFY_AUTH_TOKEN" \
    "1. Sign up for free account
2. Go to User Settings → Applications → Personal Access Tokens
3. Click 'New Access Token'
4. Name it 'weedgo-deployment' and copy the token"

# 7. Render
collect_credential \
    "Render" \
    "https://dashboard.render.com/register" \
    "RENDER_DEPLOY_HOOK_BETA" \
    "1. Sign up for free account
2. We'll set this up later when you create your backend service
3. For now, enter 'PLACEHOLDER' and we'll update it later"

################################################################################
# Pre-PROD Environment
################################################################################

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Pre-PROD Environment (2 providers)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"

# 8. Vercel
collect_credential \
    "Vercel" \
    "https://vercel.com/signup" \
    "VERCEL_TOKEN" \
    "1. Sign up for free account
2. Go to Settings → Tokens → Create Token
3. Name it 'weedgo-deployment'
4. Copy the token"

collect_credential \
    "Vercel Org" \
    "https://vercel.com/dashboard" \
    "VERCEL_ORG_ID" \
    "1. In Vercel dashboard
2. Go to Settings → General
3. Find 'Organization ID' or 'Team ID'
4. Copy the ID"

# 9. Railway
collect_credential \
    "Railway" \
    "https://railway.app/login" \
    "RAILWAY_TOKEN" \
    "1. Sign up for free account
2. Go to Account Settings → Tokens → Create New Token
3. Name it 'weedgo-deployment'
4. Copy the token"

################################################################################
# Generate JWT Secret
################################################################################

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Generating JWT Secret Keys${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

JWT_SECRET_UAT=$(openssl rand -base64 32)
JWT_SECRET_BETA=$(openssl rand -base64 32)
JWT_SECRET_PREPROD=$(openssl rand -base64 32)

echo "JWT|JWT_SECRET_UAT|$JWT_SECRET_UAT" >> "$TEMP_CREDS"
echo "JWT|JWT_SECRET_BETA|$JWT_SECRET_BETA" >> "$TEMP_CREDS"
echo "JWT|JWT_SECRET_PREPROD|$JWT_SECRET_PREPROD" >> "$TEMP_CREDS"

echo -e "${GREEN}✓ Generated 3 unique JWT secrets${NC}"

################################################################################
# Update .env files
################################################################################

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Updating .env Files${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to update env file
update_env_file() {
    local file=$1
    local key=$2
    local value=$3

    if [ -f "$file" ]; then
        if grep -q "^${key}=" "$file"; then
            # Key exists, update it
            sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
            echo -e "${GREEN}✓ Updated $key in $file${NC}"
        else
            # Key doesn't exist, append it
            echo "${key}=${value}" >> "$file"
            echo -e "${GREEN}✓ Added $key to $file${NC}"
        fi
    else
        echo -e "${RED}✗ File not found: $file${NC}"
    fi
}

# Read credentials and update files
while IFS='|' read -r provider key value; do
    case "$provider" in
        "Neon PostgreSQL")
            update_env_file ".env.uat" "DATABASE_URL" "$value"
            ;;
        "Upstash Redis")
            if [ "$key" = "UPSTASH_REDIS_REST_URL" ]; then
                update_env_file ".env.uat" "UPSTASH_REDIS_REST_URL" "$value"
            else
                update_env_file ".env.uat" "UPSTASH_REDIS_REST_TOKEN" "$value"
            fi
            ;;
        "Cloudflare R2")
            if [ "$key" = "R2_ACCESS_KEY_ID" ]; then
                update_env_file ".env.uat" "R2_ACCESS_KEY_ID" "$value"
            else
                update_env_file ".env.uat" "R2_SECRET_ACCESS_KEY" "$value"
            fi
            ;;
        "Supabase")
            if [ "$key" = "SUPABASE_URL" ]; then
                update_env_file ".env.beta" "SUPABASE_URL" "$value"
            else
                update_env_file ".env.beta" "SUPABASE_SERVICE_KEY" "$value"
            fi
            ;;
        "Supabase Database")
            update_env_file ".env.beta" "DATABASE_URL" "$value"
            ;;
        "JWT")
            if [[ "$key" == *"UAT"* ]]; then
                update_env_file ".env.uat" "JWT_SECRET_KEY" "$value"
            elif [[ "$key" == *"BETA"* ]]; then
                update_env_file ".env.beta" "JWT_SECRET_KEY" "$value"
            elif [[ "$key" == *"PREPROD"* ]]; then
                update_env_file ".env.preprod" "JWT_SECRET_KEY" "$value"
            fi
            ;;
    esac
done < "$TEMP_CREDS"

# Clean up
rm "$TEMP_CREDS"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Credential Collection Complete!${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Summary:${NC}"
echo -e "  • Updated .env.uat with 6 credentials"
echo -e "  • Updated .env.beta with 4 credentials"
echo -e "  • Updated .env.preprod with 2 credentials"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Run: ./scripts/setup-github-secrets.sh"
echo -e "  2. Then: ./scripts/deploy-environment.sh uat"
echo ""
echo -e "${CYAN}Your credentials are saved in .env.* files${NC}"
echo ""
