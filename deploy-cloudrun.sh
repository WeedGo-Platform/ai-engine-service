#!/bin/bash
#
# Quick Deploy to Google Cloud Run
# This script automates the deployment of WeedGo UAT backend to Cloud Run
#
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="weedgo-uat-2025"
REGION="us-central1"
SERVICE_NAME="weedgo-uat-backend"
REPOSITORY_NAME="weedgo-uat"
IMAGE_NAME="backend"
IMAGE_TAG="latest"

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   WeedGo UAT Backend - Cloud Run Deployment      ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check if gcloud is installed
echo -e "${YELLOW}[1/7]${NC} Checking for gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}✗ gcloud CLI not found${NC}"
    echo "Please install it: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo -e "${GREEN}✓ gcloud CLI found${NC}"
echo ""

# Step 2: Check authentication
echo -e "${YELLOW}[2/7]${NC} Checking Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}! Not authenticated. Opening browser...${NC}"
    gcloud auth login
fi
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo -e "${GREEN}✓ Authenticated as: ${ACCOUNT}${NC}"
echo ""

# Step 3: Set/Create project
echo -e "${YELLOW}[3/7]${NC} Setting up Google Cloud project..."
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${YELLOW}! Project does not exist. Creating...${NC}"
    gcloud projects create $PROJECT_ID --name="WeedGo UAT"
fi
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set: ${PROJECT_ID}${NC}"
echo ""

# Step 4: Enable APIs
echo -e "${YELLOW}[4/7]${NC} Enabling required Google Cloud APIs..."
echo "  - Cloud Run API"
gcloud services enable run.googleapis.com --quiet
echo "  - Artifact Registry API"
gcloud services enable artifactregistry.googleapis.com --quiet
echo "  - Cloud Build API"
gcloud services enable cloudbuild.googleapis.com --quiet
echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Step 5: Create Artifact Registry repository
echo -e "${YELLOW}[5/7]${NC} Setting up Artifact Registry..."
if ! gcloud artifacts repositories describe $REPOSITORY_NAME --location=$REGION &> /dev/null; then
    echo -e "${YELLOW}! Repository does not exist. Creating...${NC}"
    gcloud artifacts repositories create $REPOSITORY_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="WeedGo UAT Backend Images"
fi
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
echo -e "${GREEN}✓ Artifact Registry ready${NC}"
echo ""

# Step 6: Build and push Docker image
echo -e "${YELLOW}[6/7]${NC} Building and pushing Docker image..."
echo "This may take 10-15 minutes for first build..."
cd src/Backend

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "Building: $IMAGE_URL"

docker build -t $IMAGE_URL -f Dockerfile.uat .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_URL

echo -e "${GREEN}✓ Image pushed successfully${NC}"
echo ""

# Step 7: Deploy to Cloud Run
echo -e "${YELLOW}[7/7]${NC} Deploying to Cloud Run..."
echo "Creating/updating service: $SERVICE_NAME"

# Check if .env.cloudrun exists
if [ ! -f ".env.cloudrun" ]; then
    echo -e "${RED}✗ .env.cloudrun file not found${NC}"
    echo "Please create .env.cloudrun with your environment variables."
    echo "See CLOUD_RUN_DEPLOYMENT_GUIDE.md for details."
    exit 1
fi

gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_URL \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --env-vars-file=.env.cloudrun \
    --quiet

echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)')

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Deployment Successful!                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service URL:${NC} $SERVICE_URL"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test health endpoint:"
echo -e "   ${BLUE}curl ${SERVICE_URL}/health${NC}"
echo ""
echo "2. Test CORS:"
echo -e "   ${BLUE}curl -i -X OPTIONS '${SERVICE_URL}/api/v1/auth/admin/login' \\${NC}"
echo -e "   ${BLUE}  -H 'Origin: https://weedgo-uat-admin.pages.dev' \\${NC}"
echo -e "   ${BLUE}  -H 'Access-Control-Request-Method: POST'${NC}"
echo ""
echo "3. Update frontend environment variables with new URL"
echo ""
echo -e "${GREEN}✓ All done!${NC}"
