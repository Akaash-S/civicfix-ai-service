# Deploy via Cloud Console (Workaround for gcloud Bug)

Your gcloud CLI has a critical bug. Deploy manually via the web console instead.

## Step 1: Build and Push Image

```bash
cd ai-service

# Configure Docker
gcloud auth configure-docker

# Build image
docker build -t gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest .

# Push to registry
docker push gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest
```

## Step 2: Deploy via Cloud Console

1. **Open Cloud Run Console:**
   https://console.cloud.google.com/run?project=asolvitra-skillbridge

2. **Click "CREATE SERVICE"**

3. **Configure Container:**
   - Select: "Deploy one revision from an existing container image"
   - Click "SELECT"
   - Image URL: `gcr.io/asolvitra-skillbridge/civicfix-ai-service:latest`
   - Click "SELECT"

4. **Service Settings:**
   - Service name: `civicfix-ai-service`
   - Region: `us-central1`
   - CPU allocation: "CPU is always allocated"
   - Authentication: ✅ "Allow unauthenticated invocations"

5. **Container Settings (Click "CONTAINER, VARIABLES & SECRETS, CONNECTIONS, SECURITY"):**

   **Container Tab:**
   - Memory: `2 GiB`
   - CPU: `2`
   - Request timeout: `60` seconds
   - Maximum requests per container: `80`

   **Variables & Secrets Tab:**
   
   Click "ADD VARIABLE" for each:
   - Name: `ENABLE_MOCK_AI`, Value: `false`
   - Name: `DEBUG`, Value: `false`
   - Name: `WORKERS`, Value: `4`
   - Name: `LOG_LEVEL`, Value: `info`

   Click "REFERENCE A SECRET" for each:
   - Secret: `database-url`, Reference method: "Exposed as environment variable", Name: `DATABASE_URL`
   - Secret: `ai-service-api-key`, Reference method: "Exposed as environment variable", Name: `API_KEY`
   - Secret: `ai-service-secret-key`, Reference method: "Exposed as environment variable", Name: `SECRET_KEY`

6. **Autoscaling:**
   - Minimum instances: `1`
   - Maximum instances: `28`

7. **Click "CREATE"**

8. **Wait 2-5 minutes** for deployment to complete

## Step 3: Get Service URL

After deployment completes, you'll see the service URL at the top of the page:
`https://civicfix-ai-service-xxxxx-uc.a.run.app`

## Step 4: Test

```bash
# Replace with your actual URL
curl https://civicfix-ai-service-xxxxx-uc.a.run.app/health
```

## Alternative: Fix gcloud

If you want to fix gcloud instead:

### Option 1: Update gcloud
```bash
gcloud components update
```

### Option 2: Reinstall gcloud
1. Uninstall current gcloud
2. Download fresh installer: https://cloud.google.com/sdk/docs/install
3. Install and configure

### Option 3: Use Cloud Shell
1. Go to: https://console.cloud.google.com
2. Click the Cloud Shell icon (top right)
3. Run commands in Cloud Shell (gcloud works there)

```bash
# In Cloud Shell
git clone YOUR_REPO
cd ai-service
gcloud builds submit --config cloudbuild.yaml
```

## Summary

**Fastest solution:** Deploy via Cloud Console (Steps 1-4 above)

**Long-term solution:** Fix or reinstall gcloud CLI
