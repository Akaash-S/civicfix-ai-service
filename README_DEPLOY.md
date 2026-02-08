# CivicFix AI Service - Deployment Guide

## 🚨 gcloud Crashing? Use Cloud Shell!

If you're getting `ERROR: gcloud crashed (TypeError)`, your local gcloud is broken.

### ✅ EASIEST SOLUTION: Use Cloud Shell

1. **Open Cloud Shell:** https://console.cloud.google.com (click `>_` icon top-right)

2. **Upload your code:**
   ```bash
   # In Cloud Shell, upload the ai-service folder
   # Or clone from git if you have a repo
   ```

3. **Deploy:**
   ```bash
   cd ai-service
   gcloud builds submit --config cloudbuild.yaml --project=asolvitra-skillbridge
   ```

**Done!** Cloud Shell's gcloud always works.

---

## Alternative: Deploy via Console

If you can't use Cloud Shell:

### Step 1: Build and Push Locally
```bash
cd ai-service
gcloud auth configure-docker
docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .
docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest
```

### Step 2: Deploy via Web UI
1. Go to: https://console.cloud.google.com/run/create?project=asolvitra-skillbridge
2. Select image: `gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest`
3. Configure:
   - Service name: `civicfix-ai-service`
   - Region: `us-central1`
   - Memory: 2 GiB
   - CPU: 2
   - Max instances: 28
   - Min instances: 1
4. Add secrets: DATABASE_URL, API_KEY, SECRET_KEY
5. Add env vars: ENABLE_MOCK_AI=false, DEBUG=false, WORKERS=4, LOG_LEVEL=info
6. Click CREATE

See detailed steps: `deploy-console-only.md`

---

## Configuration

**Current Settings:**
- Memory: 2 GiB
- CPU: 2
- Max Instances: 28 (quota limit)
- Min Instances: 1
- Region: us-central1
- Project: asolvitra-skillbridge

**Required Secrets:**
- `database-url` - PostgreSQL connection string
- `ai-service-api-key` - API authentication key
- `ai-service-secret-key` - Secret key for encryption

---

## Files

### Deployment
- `cloudbuild.yaml` - Cloud Build configuration
- `Dockerfile` - Container definition

### Scripts (may not work due to gcloud bug)
- `deploy-simple.sh` - Simple deployment
- `deploy-direct.sh` - Direct deployment
- `deploy-to-gcp.sh` - Cloud Build deployment

### Documentation
- `README_DEPLOY.md` - This file
- `GCLOUD_BUG_WORKAROUND.md` - Complete workaround guide
- `deploy-console-only.md` - Console deployment steps
- `DEPLOYMENT_OPTIONS.md` - All deployment methods
- `MANUAL_DEPLOYMENT_GUIDE.md` - Detailed manual
- `QUOTA_OPTIMIZATION.md` - Resource optimization

---

## After Deployment

### Get Service URL
https://console.cloud.google.com/run/detail/us-central1/civicfix-ai-service?project=asolvitra-skillbridge

### Test
```bash
curl https://YOUR-SERVICE-URL/health
```

### View Logs
```bash
gcloud run services logs tail civicfix-ai-service --region us-central1
```

---

## Troubleshooting

### gcloud crashes
**Solution:** Use Cloud Shell or deploy via Console

### Docker not found
**Solution:** Install Docker Desktop

### Secrets not found
**Solution:** Create secrets first (see MANUAL_DEPLOYMENT_GUIDE.md)

### Quota exceeded
**Solution:** See QUOTA_OPTIMIZATION.md

---

## Quick Links

- **Cloud Shell:** https://console.cloud.google.com
- **Cloud Run Console:** https://console.cloud.google.com/run?project=asolvitra-skillbridge
- **Create Service:** https://console.cloud.google.com/run/create?project=asolvitra-skillbridge
- **View Logs:** https://console.cloud.google.com/logs?project=asolvitra-skillbridge

---

## Summary

✅ **Best Solution:** Use Cloud Shell (always works)  
✅ **Alternative:** Deploy via Console (no CLI needed)  
✅ **Long-term:** Fix local gcloud (see GCLOUD_BUG_WORKAROUND.md)  

---

**Start here:** Open Cloud Shell at https://console.cloud.google.com
