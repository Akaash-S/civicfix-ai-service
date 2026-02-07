#!/bin/bash

# CivicFix AI Service - Google Cloud Platform Deployment Script
# This script automates the deployment process to Cloud Run

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="civicfix-ai-service"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CivicFix AI Service - GCP Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Project ID not set. Please enter your GCP Project ID:${NC}"
    read -r PROJECT_ID
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}Error: Project ID is required${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Using Project ID: ${PROJECT_ID}"
echo -e "${GREEN}✓${NC} Using Region: ${REGION}"
echo ""

# Set project
echo -e "${BLUE}Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "${BLUE}Enabling required APIs...${NC}"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  --quiet

echo -e "${GREEN}✓${NC} APIs enabled"
echo ""

# Check if secrets exist, if not create them
echo -e "${BLUE}Checking secrets...${NC}"

create_secret_if_not_exists() {
    local secret_name=$1
    local secret_prompt=$2
    
    if gcloud secrets describe "$secret_name" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Secret '$secret_name' already exists"
    else
        echo -e "${YELLOW}Secret '$secret_name' not found. $secret_prompt${NC}"
        read -rs secret_value
        echo ""
        
        if [ -n "$secret_value" ]; then
            echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
            echo -e "${GREEN}✓${NC} Secret '$secret_name' created"
        else
            echo -e "${RED}Error: Secret value cannot be empty${NC}"
            exit 1
        fi
    fi
}

create_secret_if_not_exists "database-url" "Please enter your DATABASE_URL:"
create_secret_if_not_exists "ai-service-api-key" "Please enter your API_KEY:"
create_secret_if_not_exists "ai-service-secret-key" "Please enter your SECRET_KEY:"

echo ""

# Grant Cloud Run access to secrets
echo -e "${BLUE}Granting Cloud Run access to secrets...${NC}"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

for secret in database-url ai-service-api-key ai-service-secret-key; do
    gcloud secrets add-iam-policy-binding "$secret" \
      --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor" \
      --quiet 2>/dev/null || true
done

echo -e "${GREEN}✓${NC} Secrets configured"
echo ""

# Build and deploy
echo -e "${BLUE}Building and deploying to Cloud Run...${NC}"
echo "This may take 5-10 minutes..."
echo ""

gcloud builds submit --config cloudbuild.yaml

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --format 'value(status.url)')

echo -e "${GREEN}✓${NC} Service deployed successfully!"
echo ""
echo -e "${BLUE}Service URL:${NC} $SERVICE_URL"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Test the service:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "2. Update your backend .env file:"
echo "   AI_SERVICE_URL=$SERVICE_URL"
echo ""
echo "3. View logs:"
echo "   gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
echo "4. Monitor service:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo ""
echo -e "${GREEN}Deployment successful! 🚀${NC}"
