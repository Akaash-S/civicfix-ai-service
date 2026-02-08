# Quick Deployment Guide

## 🚀 Deploy in 2 Steps

### Option A: Direct Deployment (Recommended)
```bash
cd ai-service
./deploy-direct.sh
```

### Option B: Cloud Build
```bash
cd ai-service
gcloud builds submit --config cloudbuild.yaml --project=asolvitra-skillbridge
```

---

## ✅ What's Fixed

1. ✅ **Single YAML file** - Only `cloudbuild.yaml` (removed duplicates)
2. ✅ **PORT issue fixed** - Removed from env vars
3. ✅ **Quota issue fixed** - Max instances set to 28
4. ✅ **Metadata server issue** - Use `deploy-direct.sh` to avoid

---

## 📁 Files

### Deployment
- `cloudbuild.yaml` - Cloud Build config (single file)
- `deploy-direct.sh` - Direct deployment script
- `deploy-to-gcp.sh` - Cloud Build deployment script
- `Dockerfile` - Container definition

### Documentation
- `DEPLOY_README.md` - This file (quick start)
- `DEPLOYMENT_OPTIONS.md` - All deployment methods
- `MANUAL_DEPLOYMENT_GUIDE.md` - Step-by-step manual
- `QUOTA_OPTIMIZATION.md` - Resource optimization
- `DEPLOYMENT_FIX.md` - Issues and solutions

---

## 🔧 Configuration

**Current Settings:**
- Memory: 2Gi
- CPU: 2
- Max Instances: 28
- Min Instances: 1
- Region: us-central1
- Project: asolvitra-skillbridge

**Secrets (already created):**
- database-url
- ai-service-api-key
- ai-service-secret-key

---

## 🧪 Test After Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe civicfix-ai-service \
  --region us-central1 \
  --format 'value(status.url)')

# Test health
curl $SERVICE_URL/health

# Test with API key
curl -H "X-API-Key: 8209d737eb28d61c61026a61ee96326a96ebbc67ccc89ac04a8b6495f63d011b0f1053467bd9970399e7ad5e598115f1489265d916868dc55d1d687a06b33562" \
  $SERVICE_URL/api/v1/stats
```

---

## 📊 Monitor

```bash
# View logs
gcloud run services logs tail civicfix-ai-service --region us-central1

# View in console
https://console.cloud.google.com/run/detail/us-central1/civicfix-ai-service
```

---

## ❓ Having Issues?

See `DEPLOYMENT_OPTIONS.md` for:
- Troubleshooting guide
- Alternative deployment methods
- Common errors and fixes

---

**Ready to deploy? Run:** `./deploy-direct.sh`
