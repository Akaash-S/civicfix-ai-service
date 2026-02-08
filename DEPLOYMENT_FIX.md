# Cloud Run Deployment Fixes

## Issue 1: PORT Environment Variable ✅ FIXED

### Problem
```
ERROR: The following reserved env names were provided: PORT. 
These values are automatically set by the system.
```

### Solution
Removed `PORT=8080` from `--set-env-vars` in cloudbuild.yaml

---

## Issue 2: Quota Exceeded ✅ FIXED

### Problem
```
ERROR: Max instances must be set to 28 or fewer to set the requested total CPU.
Quota violated:
- CpuAllocPerProjectRegion requested: 200000 allowed: 56000
- MemAllocPerProjectRegion requested: 214748364800 allowed: 120259084288
```

### Root Cause
- Requested: 100 instances × 2 CPUs = 200 CPUs
- Allowed: 56 CPUs total
- Maximum possible: 56 ÷ 2 = **28 instances**

### Solution
Changed `--max-instances` from 100 to 28 in cloudbuild.yaml

### Your Quota Limits
- **CPU**: 56 vCPUs per region
- **Memory**: ~120 GiB per region
- **With 2 CPU per instance**: Max 28 instances
- **With 1 CPU per instance**: Max 56 instances

---

## Current Configuration ✅

```yaml
Memory: 2Gi
CPU: 2
Max Instances: 28  # Changed from 100
Min Instances: 1
Concurrency: 80
Timeout: 60s
```

**Capacity:**
- Max concurrent requests: 2,240 (28 × 80)
- Total CPU: 56 vCPUs (full quota)
- Total Memory: 56 GiB

---

## Deploy Now

```bash
cd ai-service
gcloud builds submit --config cloudbuild.yaml
```

Or:
```bash
./deploy-to-gcp.sh
```

---

## Alternative Configurations

See `QUOTA_OPTIMIZATION.md` for:
- Cost-optimized setup (1 CPU, 1 GiB)
- High concurrency setup (56 instances)
- Multi-region deployment
- Quota increase requests

---

**Status**: ✅ ALL ISSUES FIXED  
**Date**: February 2026
