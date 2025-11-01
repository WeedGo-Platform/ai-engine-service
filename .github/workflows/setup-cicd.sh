#!/bin/bash
# Setup CI/CD for WeedGo Test Environment
# This script creates the GCP service account and prepares secrets for GitHub

set -e

PROJECT_ID="weedgo-uat-2025"
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "============================================"
echo "🔧 CI/CD Setup for WeedGo Test Environment"
echo "============================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    exit 1
fi

# Verify we're in the correct project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "⚠️  Current project: $CURRENT_PROJECT"
    echo "📝 Switching to project: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
fi

echo "✓ Using project: $PROJECT_ID"
echo ""

# Check if service account already exists
if gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    echo "ℹ️  Service account $SA_NAME already exists"
else
    echo "📝 Creating service account: $SA_NAME"
    gcloud iam service-accounts create $SA_NAME \
        --display-name="GitHub Actions Deployer" \
        --description="Service account for automated GitHub Actions deployments"
    echo "✓ Service account created"
fi

echo ""
echo "🔑 Granting IAM permissions..."

# Grant required roles
roles=(
    "roles/run.admin"
    "roles/artifactregistry.writer"
    "roles/cloudsql.client"
    "roles/iam.serviceAccountUser"
)

for role in "${roles[@]}"; do
    echo "  → Granting $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --condition=None \
        --quiet &> /dev/null
done

echo "✓ All permissions granted"
echo ""

# Create service account key
KEY_FILE="/tmp/github-actions-key-$PROJECT_ID.json"
echo "🔐 Creating service account key..."

if [ -f "$KEY_FILE" ]; then
    echo "⚠️  Key file already exists at $KEY_FILE"
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing key file."
    else
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account=$SA_EMAIL
        echo "✓ New key created: $KEY_FILE"
    fi
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account=$SA_EMAIL
    echo "✓ Key created: $KEY_FILE"
fi

echo ""
echo "============================================"
echo "📋 GitHub Secrets Configuration"
echo "============================================"
echo ""
echo "Add the following secrets to your GitHub repository:"
echo ""
echo "Navigate to: Settings → Secrets and variables → Actions → New repository secret"
echo ""

# Display GCP_SA_KEY
echo "1️⃣  GCP_SA_KEY"
echo "────────────────────────────────────────────"
echo "Copy the entire contents of:"
echo "  $KEY_FILE"
echo ""
echo "Quick copy command:"
echo "  cat $KEY_FILE | pbcopy  # macOS"
echo "  cat $KEY_FILE | xclip -selection clipboard  # Linux"
echo ""

# Display CLOUD_SQL_DB_PASSWORD
if [ -f "/tmp/cloudsql-weedgo-password.txt" ]; then
    DB_PASSWORD=$(cat /tmp/cloudsql-weedgo-password.txt)
    echo "2️⃣  CLOUD_SQL_DB_PASSWORD"
    echo "────────────────────────────────────────────"
    echo "Value: $DB_PASSWORD"
    echo ""
    echo "Quick copy command:"
    echo "  echo '$DB_PASSWORD' | pbcopy  # macOS"
    echo "  echo '$DB_PASSWORD' | xclip -selection clipboard  # Linux"
    echo ""
else
    echo "2️⃣  CLOUD_SQL_DB_PASSWORD"
    echo "────────────────────────────────────────────"
    echo "⚠️  Password file not found at /tmp/cloudsql-weedgo-password.txt"
    echo "Please retrieve the password manually from Cloud SQL"
    echo ""
fi

echo "============================================"
echo "📝 Next Steps"
echo "============================================"
echo ""
echo "1. Add secrets to GitHub:"
echo "   https://github.com/WeedGo-Platform/ai-engine-service/settings/secrets/actions"
echo ""
echo "2. Push to dev branch to trigger deployment:"
echo "   git checkout dev"
echo "   git add ."
echo "   git commit -m \"feat: setup ci/cd\""
echo "   git push origin dev"
echo ""
echo "3. Monitor deployment:"
echo "   https://github.com/WeedGo-Platform/ai-engine-service/actions"
echo ""
echo "⚠️  IMPORTANT: Delete the service account key after adding to GitHub:"
echo "   rm $KEY_FILE"
echo ""
echo "✅ Setup complete!"
