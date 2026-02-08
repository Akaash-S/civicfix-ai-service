# Deployment Options for CivicFix AI Service

## Issue: gcloud Crashes with TypeError

If you see this error:
```
ERROR: gcloud crashed (TypeError): string indices must be integers, not 'str'
```

This is a gcloud bug that happens when trying to parse service information.

---

## ✅ Solution 1: Simple Deployment (EASIEST)

Use the ultra-simple script that avoids problematic gcloud commands:

```bash
cd ai-service
bash deploy-simple.sh
```

**What it does:**
1. Builds Docker image locally
2. Pushes to Google Container Registry
3. Deploys to Cloud Run
4. No gcloud describe commands (avoids the crash)

---

## ✅ Solution 2: Diagnose and Fix gcloud

Run diagnostics to find the issue:

```bash
cd ai-service
bash diagnose-gcloud.sh
```

Then try these fixes:

### Fix 1: Update gcloud
```bash
gcloud components update
```

### Fix 2: Re-authenticate
```bash
gcloud auth login
gcloud auth application-default login
```

### Fix 3: Clear gcloud cache
```bash
# Windows
rmdir /s /q %APPDATA%\gcloud

# Linux/Mac
rm -rf ~/.config/gcloud
gcloud auth login
```

---

## ✅ Solution 3: Manual Deployment (Step-by-Step)

### Step 1: Build and Push
```bash
cd ai-service

# Set project
gcloud config set project asolvitra-skillbridge

# Configure Docker
gcloud auth configure-docker

# Build
docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .

# Push
docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest
```

### Step 2: Deploy via Console

1. Go to: https://console.cloud.google.com/run
2. Click "CREATE SERVICE"
3. Select "Deploy one revision from an existing container image"
4. Image URL: `gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest`
5. Service name: `civicfix-ai-service`
6. Region: `us-central1`
7. Authentication: Allow unauthenticated
8. Container settings:
   - Memory: 2 GiB
   - CPU: 2
   - Max instances: 28
   - Min instances: 1
9. Variables & Secrets:
   - Add secrets: DATABASE_URL, API_KEY, SECRET_KEY
   - Add env vars: ENABLE_MOCK_AI=false, DEBUG=false, WORKERS=4, LOG_LEVEL=info
10. Click "CREATE"

---

## ✅ Solution 4: Cloud Build (No Local Docker)

```bash
cd ai-service
gcloud builds submit --config cloudbuild.yaml --project=asolvitra-skillbridge
```

---

## Comparison

| Method | Avoids gcloud Bug | Requires Docker | Difficulty |
|--------|-------------------|-----------------|------------|
| **deploy-simple.sh** | ✅ Yes | Yes | Easy |
| **Manual Console** | ✅ Yes | Yes (for build) | Easy |
| **Cloud Build** | ✅ Yes | No | Easy |
| **deploy-direct.sh** | ⚠️ Partial | Yes | Medium |

---

## Files Overview

### Deployment Scripts
- ✅ `deploy-simple.sh` - **RECOMMENDED** - Simplest, avoids gcloud bugs
- ✅ `deploy-direct.sh` - Full-featured with error handling
- ✅ `deploy-to-gcp.sh` - Cloud Build deployment
- ✅ `diagnose-gcloud.sh` - Diagnose gcloud issues

### Configuration
- ✅ `cloudbuild.yaml` - Cloud Build config (single file)
- ✅ `Dockerfile` - Container definition

---

## Quick Start

**Just want to deploy? Run this:**
```bash
cd ai-service
bash deploy-simple.sh
```

**Having gcloud issues? Run this first:**
```bash
bash diagnose-gcloud.sh
```

---

## After Deployment

### Get Service URL
Visit: https://console.cloud.google.com/run/detail/us-central1/civicfix-ai-service?project=asolvitra-skillbridge

### View Logs
```bash
gcloud run services logs tail civicfix-ai-service --region us-central1
```

### Test Service
```bash
# Replace with your actual service URL
curl https://civicfix-ai-service-xxxxx-uc.a.run.app/health
```

---

## Troubleshooting

### Error: "gcloud crashed"
**Solution:** Use `deploy-simple.sh` or deploy via Console

### Error: "Docker not found"
**Solution:** Install Docker or use Cloud Build method

### Error: "Secrets not found"
**Solution:** Create secrets first (see MANUAL_DEPLOYMENT_GUIDE.md)

### Error: "Quota exceeded"
**Solution:** See QUOTA_OPTIMIZATION.md

---

**Recommended:** Use `deploy-simple.sh` - it's the most reliable!
