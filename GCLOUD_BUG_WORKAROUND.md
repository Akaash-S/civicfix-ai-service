# gcloud Bug Workaround - Complete Guide

## The Problem

Your gcloud CLI is crashing with:
```
ERROR: gcloud crashed (TypeError): string indices must be integers, not 'str'
```

This is a known bug in certain gcloud versions when deploying to Cloud Run.

---

## ✅ SOLUTION 1: Deploy via Cloud Console (EASIEST)

### Step 1: Build and Push (Local)
```bash
cd ai-service
gcloud auth configure-docker
docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .
docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest
```

### Step 2: Deploy via Web Console
See detailed instructions in: `deploy-console-only.md`

Or quick link: https://console.cloud.google.com/run/create?project=asolvitra-skillbridge

---

## ✅ SOLUTION 2: Use Cloud Shell (RECOMMENDED)

Cloud Shell has a working gcloud version!

### Step 1: Open Cloud Shell
Go to: https://console.cloud.google.com
Click the terminal icon (top right): `>_`

### Step 2: Upload Your Code
In Cloud Shell:
```bash
# Option A: Clone from git (if you have a repo)
git clone YOUR_REPO_URL
cd YOUR_REPO/ai-service

# Option B: Upload files
# Click the 3-dot menu > Upload > Select ai-service folder
```

### Step 3: Deploy from Cloud Shell
```bash
cd ai-service

# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml --project=asolvitra-skillbridge

# Or deploy directly
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
  --set-env-vars="ENABLE_MOCK_AI=false,DEBUG=false,WORKERS=4,LOG_LEVEL=info" \
  --project=asolvitra-skillbridge
```

---

## ✅ SOLUTION 3: Fix Your Local gcloud

### Option A: Update gcloud
```bash
gcloud components update
gcloud version
```

### Option B: Reinstall gcloud
1. **Uninstall current gcloud:**
   - Windows: Control Panel > Uninstall Programs > Google Cloud SDK
   - Mac: `rm -rf ~/google-cloud-sdk`
   - Linux: `rm -rf ~/google-cloud-sdk`

2. **Download fresh installer:**
   https://cloud.google.com/sdk/docs/install

3. **Install and configure:**
   ```bash
   gcloud init
   gcloud auth login
   gcloud config set project asolvitra-skillbridge
   ```

### Option C: Use Different gcloud Version
```bash
# Install specific version
gcloud components update --version=450.0.0
```

---

## ✅ SOLUTION 4: Use REST API Directly

If all else fails, deploy using curl and the Cloud Run API:

```bash
# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Deploy via REST API
curl -X POST \
  "https://run.googleapis.com/v2/projects/asolvitra-skillbridge/locations/us-central1/services" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "civicfix-ai-service",
    "template": {
      "containers": [{
        "image": "gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest",
        "resources": {
          "limits": {
            "memory": "2Gi",
            "cpu": "2"
          }
        },
        "env": [
          {"name": "ENABLE_MOCK_AI", "value": "false"},
          {"name": "DEBUG", "value": "false"},
          {"name": "WORKERS", "value": "4"},
          {"name": "LOG_LEVEL", "value": "info"}
        ]
      }],
      "scaling": {
        "minInstanceCount": 1,
        "maxInstanceCount": 28
      }
    }
  }'
```

---

## Comparison

| Solution | Difficulty | Requires | Success Rate |
|----------|-----------|----------|--------------|
| **Cloud Console** | Easy | Docker locally | 99% |
| **Cloud Shell** | Easy | Nothing | 99% |
| **Fix gcloud** | Medium | Time | 70% |
| **REST API** | Hard | curl knowledge | 90% |

---

## Recommended Approach

1. **Try Cloud Shell first** (Solution 2)
   - Always works
   - No local issues
   - Fast

2. **If you need local deployment:**
   - Build/push locally
   - Deploy via Console (Solution 1)

3. **Long-term:**
   - Fix your local gcloud (Solution 3)

---

## After Deployment

### Get Service URL
https://console.cloud.google.com/run/detail/us-central1/civicfix-ai-service?project=asolvitra-skillbridge

### Test Service
```bash
curl https://YOUR-SERVICE-URL/health
```

### View Logs
```bash
gcloud run services logs tail civicfix-ai-service --region us-central1
```

---

## Why This Happens

The gcloud bug occurs when:
- Parsing JSON responses from Cloud Run API
- Certain gcloud versions (especially older ones)
- Windows systems more affected
- Corrupted gcloud cache

---

## Prevention

To avoid this in the future:
1. Keep gcloud updated: `gcloud components update`
2. Use Cloud Shell for critical deployments
3. Have CI/CD pipeline (GitHub Actions, Cloud Build triggers)

---

## Need Help?

1. Check gcloud version: `gcloud version`
2. Run diagnostics: `gcloud info --run-diagnostics`
3. Check logs: `%APPDATA%\gcloud\logs` (Windows)

---

**RECOMMENDED: Use Cloud Shell - it always works!**

Open Cloud Shell: https://console.cloud.google.com
