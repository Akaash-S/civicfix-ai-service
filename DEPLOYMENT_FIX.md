# Cloud Run Deployment Fix - PORT Environment Variable Issue

## Problem
```
ERROR: (gcloud.run.deploy) spec.template.spec.containers[0].env: 
The following reserved env names were provided: PORT. 
These values are automatically set by the system.
```

## Root Cause
Cloud Run **automatically sets the `PORT` environment variable** and does not allow manual override. The deployment was failing because we tried to set `PORT=8080` in the `--set-env-vars` flag.

## Solution Applied

### 1. Fixed `cloudbuild.yaml`
**Before:**
```yaml
- '--set-env-vars'
- 'PORT=8080,ENABLE_MOCK_AI=false,DEBUG=false,WORKERS=4,LOG_LEVEL=info'
```

**After:**
```yaml
- '--set-env-vars'
- 'ENABLE_MOCK_AI=false,DEBUG=false,WORKERS=4,LOG_LEVEL=info'
```

### 2. Updated `Dockerfile`
The Dockerfile already correctly uses `${PORT:-8080}` in the CMD, which allows Cloud Run to inject its own PORT value:
```dockerfile
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

- Cloud Run will inject `PORT` at runtime (usually 8080)
- The `:-8080` provides a fallback for local development
- Removed HEALTHCHECK as Cloud Run has its own health checking mechanism

### 3. Updated Documentation
- Fixed `MANUAL_DEPLOYMENT_GUIDE.md` to remove PORT from env vars
- Updated `cloudbuild-no-secrets.yaml` for testing

## How Cloud Run PORT Works

1. **Cloud Run automatically sets PORT** - You cannot override it
2. **Default value is 8080** - But Cloud Run may use other ports
3. **Your app must listen on $PORT** - Not a hardcoded port
4. **Dockerfile can set default** - `ENV PORT=8080` is fine for local dev
5. **CMD must use variable** - `--port ${PORT}` or `--port $PORT`

## Deploy Now

Your deployment should now work:

```bash
# From ai-service directory
gcloud builds submit --config cloudbuild.yaml
```

Or use the automated script:
```bash
./deploy-to-gcp.sh
```

## Verification

After deployment succeeds, test:
```bash
SERVICE_URL=$(gcloud run services describe civicfix-ai-service \
  --region us-central1 \
  --format 'value(status.url)')

curl $SERVICE_URL/health
```

## Key Takeaways

✅ **DO**: Let Cloud Run set PORT automatically  
✅ **DO**: Use `${PORT}` variable in your CMD  
✅ **DO**: Set default in Dockerfile for local dev  

❌ **DON'T**: Set PORT in `--set-env-vars`  
❌ **DON'T**: Hardcode port in CMD  
❌ **DON'T**: Override PORT in Cloud Run config  

## Reserved Environment Variables in Cloud Run

Cloud Run automatically sets these - **DO NOT override**:
- `PORT` - The port your app should listen on
- `K_SERVICE` - The name of the Cloud Run service
- `K_REVISION` - The name of the Cloud Run revision
- `K_CONFIGURATION` - The name of the configuration

## Additional Resources

- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Run Container Contract](https://cloud.google.com/run/docs/container-contract)

---

**Status**: ✅ FIXED  
**Date**: February 2026  
**Issue**: PORT environment variable conflict  
**Resolution**: Removed PORT from --set-env-vars in cloudbuild.yaml
