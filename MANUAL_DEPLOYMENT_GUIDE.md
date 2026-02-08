# Manual Deployment Guide - CivicFix AI Service to Google Cloud Platform

This guide walks you through deploying the AI service manually to Google Cloud Run.

## Prerequisites

1. **Google Cloud SDK (gcloud)** installed
   - Download from: https://cloud.google.com/sdk/docs/install
   - Verify: `gcloud --version`

2. **Docker** installed (for local testing)
   - Download from: https://docs.docker.com/get-docker/

3. **GCP Project** created
   - Create at: https://console.cloud.google.com/

4. **Billing enabled** on your GCP project

---

## Step 1: Initial Setup

### 1.1 Login to Google Cloud
```bash
gcloud auth login
```

### 1.2 Set Your Project ID
```bash
# Replace with your actual project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 1.3 Set Region
```bash
export REGION="us-central1"
gcloud config set run/region $REGION
```

### 1.4 Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com
```

---

## Step 2: Create Secrets

### 2.1 Create Database URL Secret
```bash
# Replace with your actual Neon PostgreSQL connection string
echo -n "postgresql://user:password@host/database?sslmode=require" | \
  gcloud secrets create database-url --data-file=-
```

**Your Database URL:**
```
postgresql://neondb_owner:npg_SOe1wmKF2pIT@ep-sweet-bird-a160p4lr-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### 2.2 Create API Key Secret
```bash
echo -n "8209d737eb28d61c61026a61ee96326a96ebbc67ccc89ac04a8b6495f63d011b0f1053467bd9970399e7ad5e598115f1489265d916868dc55d1d687a06b33562" | \
  gcloud secrets create ai-service-api-key --data-file=-
```

### 2.3 Create Secret Key Secret
```bash
echo -n "5f8b19bd04ecdb551bd922ee7094a68b0ed859fa03f8f7fbc13da29a49e4afece25e2bba3af8d6413a5607d869eb29a4637887fe6222ddd612c277a76e28969f" | \
  gcloud secrets create ai-service-secret-key --data-file=-
```

### 2.4 Grant Cloud Run Access to Secrets
```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant access to each secret
for secret in database-url ai-service-api-key ai-service-secret-key; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

---

## Step 3: Build and Push Docker Image

### 3.1 Navigate to AI Service Directory
```bash
cd ai-service
```

### 3.2 Build Docker Image Locally (Optional - for testing)
```bash
docker build -t civicfix-ai-service:test .
docker run -p 8001:8080 -e PORT=8080 civicfix-ai-service:test
# Test at http://localhost:8001/health
```

### 3.3 Build and Push to Google Container Registry
```bash
# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/civicfix-ai-service:latest

# Or use Cloud Build with cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml
```

---

## Step 4: Deploy to Cloud Run

### 4.1 Deploy the Service
```bash
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --max-instances 28 \
  --min-instances 1 \
  --concurrency 80 \
  --set-secrets "DATABASE_URL=database-url:latest,API_KEY=ai-service-api-key:latest,SECRET_KEY=ai-service-secret-key:latest" \
  --set-env-vars "ENABLE_MOCK_AI=false,DEBUG=false,WORKERS=4,LOG_LEVEL=info"
```

### 4.2 Wait for Deployment
The deployment will take 2-5 minutes. You'll see output like:
```
Deploying container to Cloud Run service [civicfix-ai-service] in project [your-project] region [us-central1]
✓ Deploying... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [civicfix-ai-service] revision [civicfix-ai-service-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://civicfix-ai-service-xxxxx-uc.a.run.app
```

---

## Step 5: Verify Deployment

### 5.1 Get Service URL
```bash
SERVICE_URL=$(gcloud run services describe civicfix-ai-service \
  --region $REGION \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 5.2 Test Health Endpoint
```bash
curl $SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "fake_detection": "enabled",
    "duplicate_detection": "enabled",
    "location_validation": "enabled",
    "category_validation": "enabled"
  }
}
```

### 5.3 Test with API Key
```bash
curl -X GET "$SERVICE_URL/api/v1/stats" \
  -H "X-API-Key: 8209d737eb28d61c61026a61ee96326a96ebbc67ccc89ac04a8b6495f63d011b0f1053467bd9970399e7ad5e598115f1489265d916868dc55d1d687a06b33562"
```

---

## Step 6: Update Backend Configuration

### 6.1 Update Backend .env File
Add the service URL to your backend `.env` file:
```bash
AI_SERVICE_URL=https://civicfix-ai-service-xxxxx-uc.a.run.app
AI_SERVICE_API_KEY=8209d737eb28d61c61026a61ee96326a96ebbc67ccc89ac04a8b6495f63d011b0f1053467bd9970399e7ad5e598115f1489265d916868dc55d1d687a06b33562
AI_SERVICE_ENABLED=true
```

---

## Step 7: Monitor and Manage

### 7.1 View Logs
```bash
# Stream logs in real-time
gcloud run services logs tail civicfix-ai-service --region $REGION

# View recent logs
gcloud run services logs read civicfix-ai-service --region $REGION --limit 50
```

### 7.2 View Service Details
```bash
gcloud run services describe civicfix-ai-service --region $REGION
```

### 7.3 Open in Cloud Console
```bash
# Open service in browser
gcloud run services browse civicfix-ai-service --region $REGION

# Or visit directly:
# https://console.cloud.google.com/run/detail/us-central1/civicfix-ai-service
```

### 7.4 View Metrics
Visit: https://console.cloud.google.com/run/detail/$REGION/civicfix-ai-service/metrics

---

## Step 8: Update Deployment

### 8.1 Rebuild and Redeploy
```bash
# Build new image
gcloud builds submit --tag gcr.io/$PROJECT_ID/civicfix-ai-service:latest

# Deploy will automatically use the new image
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region $REGION
```

### 8.2 Update Environment Variables Only
```bash
gcloud run services update civicfix-ai-service \
  --region $REGION \
  --set-env-vars "DEBUG=true,LOG_LEVEL=debug"
```

### 8.3 Update Secrets
```bash
# Update a secret value
echo -n "new-secret-value" | gcloud secrets versions add database-url --data-file=-

# Cloud Run will automatically use the latest version
```

---

## Step 9: Scaling Configuration

### 9.1 Update Scaling Settings
```bash
gcloud run services update civicfix-ai-service \
  --region $REGION \
  --min-instances 2 \
  --max-instances 200 \
  --concurrency 100
```

### 9.2 Update Resource Limits
```bash
gcloud run services update civicfix-ai-service \
  --region $REGION \
  --memory 4Gi \
  --cpu 4
```

---

## Step 10: Troubleshooting

### 10.1 Service Not Starting
```bash
# Check logs for errors
gcloud run services logs read civicfix-ai-service --region $REGION --limit 100

# Check service status
gcloud run services describe civicfix-ai-service --region $REGION
```

### 10.2 Secret Access Issues
```bash
# Verify secrets exist
gcloud secrets list

# Check IAM permissions
gcloud secrets get-iam-policy database-url
```

### 10.3 Build Failures
```bash
# View build logs
gcloud builds list --limit 5

# Get specific build details
gcloud builds describe BUILD_ID
```

### 10.4 Connection Issues
```bash
# Test from Cloud Shell
curl https://civicfix-ai-service-xxxxx-uc.a.run.app/health

# Check firewall rules (if using VPC)
gcloud compute firewall-rules list
```

---

## Step 11: Cost Optimization

### 11.1 Set Budget Alerts
1. Go to: https://console.cloud.google.com/billing/budgets
2. Create budget alert for Cloud Run costs

### 11.2 Monitor Usage
```bash
# View current month costs
gcloud billing accounts list
```

### 11.3 Reduce Costs
- Set `--min-instances 0` for development (cold starts)
- Use smaller memory/CPU for testing
- Set request timeout lower if possible

---

## Step 12: Security Best Practices

### 12.1 Restrict Access (Optional)
```bash
# Remove public access
gcloud run services remove-iam-policy-binding civicfix-ai-service \
  --region $REGION \
  --member="allUsers" \
  --role="roles/run.invoker"

# Add specific service account
gcloud run services add-iam-policy-binding civicfix-ai-service \
  --region $REGION \
  --member="serviceAccount:backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 12.2 Rotate Secrets Regularly
```bash
# Generate new API key
NEW_API_KEY=$(openssl rand -hex 64)

# Update secret
echo -n "$NEW_API_KEY" | gcloud secrets versions add ai-service-api-key --data-file=-

# Update backend configuration
```

---

## Quick Reference Commands

```bash
# Deploy
gcloud builds submit --config cloudbuild.yaml

# View logs
gcloud run services logs tail civicfix-ai-service --region us-central1

# Get URL
gcloud run services describe civicfix-ai-service --region us-central1 --format 'value(status.url)'

# Update env vars
gcloud run services update civicfix-ai-service --region us-central1 --set-env-vars "KEY=value"

# Delete service
gcloud run services delete civicfix-ai-service --region us-central1

# List all services
gcloud run services list
```

---

## Support

- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Pricing Calculator**: https://cloud.google.com/products/calculator
- **Support**: https://cloud.google.com/support

---

## Notes

- **Region**: `us-central1` is used by default. Change if needed for lower latency.
- **Costs**: Cloud Run charges for CPU/memory usage and requests. Monitor your usage.
- **Cold Starts**: With `min-instances=1`, the service is always warm (no cold starts).
- **Secrets**: Never commit secrets to git. Always use Secret Manager.
- **API Key**: The X-API-Key header is required for all API endpoints except `/health`.

---

**Last Updated**: February 2026
**Service Version**: 1.0.0
