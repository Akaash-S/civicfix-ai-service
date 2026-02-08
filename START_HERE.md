# 🚀 START HERE - Deploy CivicFix AI Service

## Your gcloud is broken. Here's the fix:

---

## ✅ SOLUTION: Use Cloud Shell (2 minutes)

### Step 1: Open Cloud Shell
Click here: https://console.cloud.google.com

Click the terminal icon `>_` in the top-right corner

### Step 2: Upload Your Code
In Cloud Shell, click the 3-dot menu (⋮) > "Upload" > "Upload folder"

Select your `ai-service` folder

### Step 3: Deploy
In Cloud Shell terminal, run:
```bash
cd ai-service
gcloud builds submit --config cloudbuild.yaml --project=asolvitra-skillbridge
```

### Step 4: Wait
Deployment takes 5-10 minutes. You'll see:
```
✓ Deploying... Done.
Service URL: https://civicfix-ai-service-xxxxx-uc.a.run.app
```

### Step 5: Test
```bash
curl https://civicfix-ai-service-xxxxx-uc.a.run.app/health
```

---

## ✅ ALTERNATIVE: Deploy via Console

### Step 1: Build Locally
```bash
cd ai-service
docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .
gcloud auth configure-docker
docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest
```

### Step 2: Deploy via Web
1. Go to: https://console.cloud.google.com/run/create?project=asolvitra-skillbridge
2. Image: `gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest`
3. Service name: `civicfix-ai-service`
4. Region: `us-central1`
5. Memory: 2 GiB, CPU: 2
6. Max instances: 28, Min: 1
7. Add secrets: DATABASE_URL, API_KEY, SECRET_KEY
8. Add env vars: ENABLE_MOCK_AI=false, DEBUG=false, WORKERS=4, LOG_LEVEL=info
9. Click CREATE

---

## 📚 More Help

- **Detailed Console Steps:** `deploy-console-only.md`
- **All Workarounds:** `GCLOUD_BUG_WORKAROUND.md`
- **Full Guide:** `README_DEPLOY.md`

---

## 🎯 Recommended

**Use Cloud Shell** - It's the fastest and most reliable!

Open now: https://console.cloud.google.com
