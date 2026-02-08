# Quick Deployment Guide

## 🚀 Deploy Now (Simplest Method)

```bash
cd ai-service
bash deploy-simple.sh
```

**This avoids all gcloud bugs!**

---

## 🔧 Having gcloud Issues?

If you get `ERROR: gcloud crashed (TypeError)`:

### Option 1: Use Simple Deploy (Recommended)
```bash
bash deploy-simple.sh
```

### Option 2: Diagnose gcloud
```bash
bash diagnose-gcloud.sh
```

Then try:
```bash
gcloud components update
gcloud auth login
```

### Option 3: Deploy via Console
1. Build: `docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .`
2. Push: `docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest`
3. Go to: https://console.cloud.google.com/run
4. Click "CREATE SERVICE" and configure manually

---

## 📁 Deployment Scripts

- `deploy-simple.sh` - **RECOMMENDED** - Simplest, most reliable
- `deploy-direct.sh` - Full-featured with error handling
- `deploy-to-gcp.sh` - Cloud Build deployment
- `diagnose-gcloud.sh` - Diagnose gcloud issues

---

## ✅ What's Fixed

1. ✅ **Single YAML file** - Only `cloudbuild.yaml`
2. ✅ **PORT issue fixed** - Removed from env vars
3. ✅ **Quota issue fixed** - Max instances set to 28
4. ✅ **gcloud crash avoided** - Use `deploy-simple.sh`

---

## 🧪 Test After Deployment

Visit the Cloud Console to get your service URL:
https://console.cloud.google.com/run/detail/us-central1/civicfix-ai-service?project=asolvitra-skillbridge

Then test:
```bash
# Replace with your actual URL
curl https://civicfix-ai-service-xxxxx-uc.a.run.app/health
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

## ❓ Need Help?

See `DEPLOYMENT_OPTIONS.md` for:
- All deployment methods
- Troubleshooting guide
- Alternative approaches

---

**Ready to deploy? Run:** `bash deploy-simple.sh`
