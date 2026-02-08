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
gcloud config set project "$PROJECT_ID" --quiet

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

# Deploy to Cloud Run with explicit format to avoid gcloud crash
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
echo "This may take 2-5 minutes..."
echo ""

# Deploy without --quiet to see progress
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
  --project="$PROJECT_ID"

DEPLOY_EXIT_CODE=$?

if [ $DEPLOY_EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}Deployment failed with exit code: $DEPLOY_EXIT_CODE${NC}"
    echo ""
    echo "Common issues:"
    echo "1. Secrets not created - Run: gcloud secrets list"
    echo "2. Quota exceeded - See QUOTA_OPTIMIZATION.md"
    echo "3. Region not available - Try: --region=us-east1"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Try to get service URL with error handling
echo -e "${BLUE}Retrieving service URL...${NC}"

# Method 1: Try with format flag
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format='value(status.url)' 2>/dev/null || echo "")

# Method 2: If that fails, try without format
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
      --region="$REGION" \
      --project="$PROJECT_ID" 2>/dev/null | grep -oP 'https://[^\s]+' | head -1 || echo "")
fi

# Method 3: Construct URL manually
if [ -z "$SERVICE_URL" ]; then
    echo -e "${YELLOW}⚠${NC} Could not retrieve URL automatically"
    echo ""
    echo "Your service is deployed! Find the URL here:"
    echo "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
    echo ""
    echo "Or run manually:"
    echo "gcloud run services describe $SERVICE_NAME --region $REGION"
else
    echo -e "${GREEN}✓${NC} Service URL: $SERVICE_URL"
    echo ""
    
    # Test health endpoint
    echo -e "${BLUE}Testing health endpoint...${NC}"
    sleep 5
    
    HEALTH_RESPONSE=$(curl -f -s "$SERVICE_URL/health" 2>&1 || echo "failed")
    
    if [[ "$HEALTH_RESPONSE" != "failed" ]]; then
        echo -e "${GREEN}✓${NC} Health check passed!"
        echo ""
        echo "Response:"
        echo "$HEALTH_RESPONSE" | head -5
    else
        echo -e "${YELLOW}⚠${NC} Health check failed (service may still be starting)"
        echo "Wait 30 seconds and try: curl $SERVICE_URL/health"
    fi
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. View in console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo "2. View logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo "3. Test API: curl -H 'X-API-Key: YOUR_KEY' \$SERVICE_URL/api/v1/stats"
echo ""
echo -e "${GREEN}Deployment successful! 🚀${NC}"
