# Deployment Options for CivicFix AI Service

## Issue: Metadata Server Timeout

If you see this error:
```
WARNING: Compute Engine Metadata server unavailable
ERROR: gcloud crashed (TypeError): string indices must be integers, not 'str'
```

This happens when running `gcloud builds submit` from a local machine (not in GCP).

---

## ✅ Solution 1: Direct Deployment (RECOMMENDED)

Use the direct deployment script that builds locally and pushes to Cloud Run:

```bash
cd ai-service
chmod +x deploy-direct.sh
./deploy-direct.sh
```

**What it does:**
1. Builds Docker image locally
2. Pushes to Google Container Registry
3. Deploys directly to Cloud Run
4. No Cloud Build needed!

**Requirements:**
- Docker installed locally
- gcloud CLI configured
- Sufficient local disk space (~2GB)

---

## ✅ Solution 2: Cloud Build (Original Method)

Use Cloud Build to build and deploy (runs in GCP, not locally):

```bash
cd ai-service
gcloud builds submit --config cloudbuild.yaml --project=asolvitra-skillbridge
```

**What it does:**
1. Uploads source code to GCP
2. Builds in Cloud Build (remote)
3. Deploys to Cloud Run
4. No local Docker needed

**Requirements:**
- Cloud Build API enabled
- Sufficient Cloud Build quota

---

## ✅ Solution 3: Manual Step-by-Step

### Step 1: Build locally
```bash
cd ai-service
docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .
```

### Step 2: Configure Docker auth
```bash
gcloud auth configure-docker
```

### Step 3: Push to GCR
```bash
docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest
```

### Step 4: Deploy to Cloud Run
```bash
gcloud run deploy civicfix-ai-service \
  --image=gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=60 \
  --max-instances=28 \
  --min-instances=1 \
  --concurrency=80 \
  --set-secrets="DATABASE_URL=database-url:latest,API_KEY=ai-service-api-key:latest,SECRET_KEY=ai-service-secret-key:latest" \
  --set-env-vars="ENABLE_MOCK_AI=false,DEBUG=false,WORKERS=4,LOG_LEVEL=info"
```

---

## Comparison

| Method | Build Location | Speed | Requires Docker | Best For |
|--------|---------------|-------|-----------------|----------|
| **Direct Deploy** | Local | Fast | Yes | Development, Quick updates |
| **Cloud Build** | GCP | Medium | No | CI/CD, Production |
| **Manual** | Local | Slow | Yes | Troubleshooting |

---

## Files Overview

### Single Deployment File
- ✅ `cloudbuild.yaml` - Cloud Build configuration (only one file now)

### Deployment Scripts
- ✅ `deploy-direct.sh` - Direct deployment (local build)
- ✅ `deploy-to-gcp.sh` - Cloud Build deployment (remote build)

### Documentation
- ✅ `DEPLOYMENT_OPTIONS.md` - This file
- ✅ `MANUAL_DEPLOYMENT_GUIDE.md` - Detailed manual steps
- ✅ `QUOTA_OPTIMIZATION.md` - Resource optimization
- ✅ `DEPLOYMENT_FIX.md` - Common issues and fixes

---

## Recommended Workflow

### For Development
```bash
./deploy-direct.sh
```
- Fast iteration
- Build locally
- See errors immediately

### For Production
```bash
gcloud builds submit --config cloudbuild.yaml
```
- Consistent builds
- No local dependencies
- Automated CI/CD ready

---

## Troubleshooting

### Error: "Metadata server unavailable"
**Solution:** Use `deploy-direct.sh` instead of Cloud Build

### Error: "Docker not found"
**Solution:** Install Docker or use Cloud Build method

### Error: "Permission denied"
**Solution:** 
```bash
chmod +x deploy-direct.sh
# Or on Windows:
bash deploy-direct.sh
```

### Error: "Image push failed"
**Solution:**
```bash
gcloud auth configure-docker
gcloud auth login
```

### Error: "Quota exceeded"
**Solution:** See `QUOTA_OPTIMIZATION.md`

---

## Quick Commands

### Check deployment status
```bash
gcloud run services describe civicfix-ai-service --region us-central1
```

### View logs
```bash
gcloud run services logs tail civicfix-ai-service --region us-central1
```

### Get service URL
```bash
gcloud run services describe civicfix-ai-service \
  --region us-central1 \
  --format 'value(status.url)'
```

### Test health endpoint
```bash
SERVICE_URL=$(gcloud run services describe civicfix-ai-service \
  --region us-central1 \
  --format 'value(status.url)')
curl $SERVICE_URL/health
```

---

## Summary

✅ **Use `deploy-direct.sh`** - Fastest, most reliable for local development  
✅ **Use `cloudbuild.yaml`** - Best for CI/CD and production  
✅ **Single YAML file** - No confusion, one source of truth  

---

**Last Updated:** February 2026  
**Status:** All deployment methods working
