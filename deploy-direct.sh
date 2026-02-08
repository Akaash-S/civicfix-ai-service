#!/bin/bash

# Direct Cloud Run Deployment (No Cloud Build)
# Use this if Cloud Build is having issues

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-asolvitra-skillbridge}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="civicfix-ai-service"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Direct Cloud Run Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Project ID: $PROJECT_ID"
echo -e "${GREEN}✓${NC} Region: $REGION"
echo -e "${GREEN}✓${NC} Service: $SERVICE_NAME"
echo ""

# Set project
echo -e "${BLUE}Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"

# Configure Docker for GCR
echo -e "${BLUE}Configuring Docker authentication...${NC}"
gcloud auth configure-docker --quiet

# Build image locally
echo -e "${BLUE}Building Docker image locally...${NC}"
docker build -t "$IMAGE_NAME" .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Image built successfully"
echo ""

# Push to GCR
echo -e "${BLUE}Pushing image to Container Registry...${NC}"
docker push "$IMAGE_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker push failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Image pushed successfully"
echo ""

# Deploy to Cloud Run
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE_NAME" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=60 \
  --max-instances=28 \
  --min-instances=1 \
  --concurrency=80 \
  --set-secrets="DATABASE_URL=database-url:latest,API_KEY=ai-service-api-key:latest,SECRET_KEY=ai-service-secret-key:latest" \
  --set-env-vars="ENABLE_MOCK_AI=false,DEBUG=false,WORKERS=4,LOG_LEVEL=info" \
  --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}Deployment failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --format 'value(status.url)' 2>/dev/null)

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}✓${NC} Service URL: $SERVICE_URL"
    echo ""
    
    # Test health endpoint
    echo -e "${BLUE}Testing health endpoint...${NC}"
    sleep 5
    
    if curl -f -s "$SERVICE_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Health check passed!"
    else
        echo -e "${YELLOW}⚠${NC} Health check failed (service may still be starting)"
    fi
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Test: curl $SERVICE_URL/health"
echo "2. View logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo "3. Monitor: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo ""
echo -e "${GREEN}Deployment successful! 🚀${NC}"
