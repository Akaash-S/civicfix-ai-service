#!/bin/bash

# Simplest Cloud Run Deployment
# Avoids all gcloud describe commands that might crash

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ID="asolvitra-skillbridge"
REGION="us-central1"
SERVICE_NAME="civicfix-ai-service"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

echo -e "${BLUE}=== CivicFix AI Service Deployment ===${NC}"
echo ""

# Step 1: Set project
echo -e "${BLUE}[1/5] Setting project...${NC}"
gcloud config set project "$PROJECT_ID" --quiet
echo -e "${GREEN}✓${NC} Done"
echo ""

# Step 2: Configure Docker
echo -e "${BLUE}[2/5] Configuring Docker...${NC}"
gcloud auth configure-docker --quiet
echo -e "${GREEN}✓${NC} Done"
echo ""

# Step 3: Build
echo -e "${BLUE}[3/5] Building image...${NC}"
docker build -t "$IMAGE_NAME" . || {
    echo -e "${RED}Build failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓${NC} Done"
echo ""

# Step 4: Push
echo -e "${BLUE}[4/5] Pushing to registry...${NC}"
docker push "$IMAGE_NAME" || {
    echo -e "${RED}Push failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓${NC} Done"
echo ""

# Step 5: Deploy
echo -e "${BLUE}[5/5] Deploying to Cloud Run...${NC}"
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
  --project="$PROJECT_ID" || {
    echo ""
    echo -e "${RED}Deployment failed!${NC}"
    echo ""
    echo "Check if secrets exist:"
    echo "  gcloud secrets list --project=$PROJECT_ID"
    echo ""
    exit 1
}

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "View your service:"
echo "  https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo ""
echo "View logs:"
echo "  gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
echo -e "${GREEN}Done! 🚀${NC}"
