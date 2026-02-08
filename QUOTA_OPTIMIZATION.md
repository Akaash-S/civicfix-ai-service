# Cloud Run Quota Optimization Guide

## Current Issue
```
ERROR: Max instances must be set to 28 or fewer to set the requested total CPU.
Quota violated:
- CpuAllocPerProjectRegion requested: 200000 allowed: 56000
- MemAllocPerProjectRegion requested: 214748364800 allowed: 120259084288
```

## Your Current Quota Limits
- **CPU**: 56 vCPUs total
- **Memory**: ~120 GiB total
- **Region**: us-central1

## Configuration Options

### Option 1: Maximum Performance (Within Quota) ✅ APPLIED
**Best for: Production with high traffic**

```yaml
--memory 2Gi
--cpu 2
--max-instances 28
--min-instances 1
--concurrency 80
```

**Capacity:**
- Max instances: 28
- Total CPU: 56 vCPUs (at quota limit)
- Total Memory: 56 GiB
- Max concurrent requests: 2,240 (28 × 80)

**Cost:** ~$40-60/month with moderate traffic

---

### Option 2: Balanced (Recommended for Most Cases)
**Best for: Production with moderate traffic**

```yaml
--memory 2Gi
--cpu 2
--max-instances 10
--min-instances 0
--concurrency 80
```

**Capacity:**
- Max instances: 10
- Total CPU: 20 vCPUs
- Total Memory: 20 GiB
- Max concurrent requests: 800 (10 × 80)

**Cost:** ~$15-25/month with moderate traffic

**Deploy:**
```bash
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80
```

---

### Option 3: Cost-Optimized
**Best for: Development/Testing or low traffic**

```yaml
--memory 1Gi
--cpu 1
--max-instances 10
--min-instances 0
--concurrency 80
```

**Capacity:**
- Max instances: 10
- Total CPU: 10 vCPUs
- Total Memory: 10 GiB
- Max concurrent requests: 800 (10 × 80)

**Cost:** ~$8-15/month with low traffic

**Deploy:**
```bash
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80
```

---

### Option 4: High Concurrency (More Instances, Less Resources)
**Best for: Many small requests**

```yaml
--memory 1Gi
--cpu 1
--max-instances 56
--min-instances 0
--concurrency 100
```

**Capacity:**
- Max instances: 56 (uses full CPU quota)
- Total CPU: 56 vCPUs
- Total Memory: 56 GiB
- Max concurrent requests: 5,600 (56 × 100)

**Cost:** ~$30-50/month with high traffic

**Deploy:**
```bash
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 56 \
  --min-instances 0 \
  --concurrency 100
```

---

## Quota Calculation Formula

```
Max Instances = MIN(
  CPU_QUOTA / CPU_PER_INSTANCE,
  MEMORY_QUOTA / MEMORY_PER_INSTANCE
)
```

**Your limits:**
- CPU: 56 ÷ 2 = **28 instances** (with 2 CPU)
- CPU: 56 ÷ 1 = **56 instances** (with 1 CPU)
- Memory: 120 ÷ 2 = **60 instances** (with 2 GiB)
- Memory: 120 ÷ 1 = **120 instances** (with 1 GiB)

---

## Request Quota Increase

If you need more capacity, request a quota increase:

### 1. Via Cloud Console
1. Go to: https://console.cloud.google.com/iam-admin/quotas
2. Filter: "Cloud Run API"
3. Select: "CPU allocation per region"
4. Click "EDIT QUOTAS"
5. Request new limit (e.g., 200 CPUs)

### 2. Via gcloud
```bash
# Check current quotas
gcloud compute project-info describe --project=$PROJECT_ID

# Request increase (requires manual approval)
# Visit: https://cloud.google.com/run/quotas#requesting_higher_quota
```

**Typical approval time:** 2-3 business days

---

## Multi-Region Deployment

Deploy to multiple regions to distribute load:

```bash
# Deploy to us-central1
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region us-central1 \
  --max-instances 28

# Deploy to us-east1 (separate quota)
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region us-east1 \
  --max-instances 28

# Deploy to europe-west1 (separate quota)
gcloud run deploy civicfix-ai-service \
  --image gcr.io/$PROJECT_ID/civicfix-ai-service:latest \
  --region europe-west1 \
  --max-instances 28
```

**Total capacity:** 84 instances across 3 regions

---

## Monitoring and Alerts

### Check Current Usage
```bash
# View service details
gcloud run services describe civicfix-ai-service --region us-central1

# View metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/instance_count"'
```

### Set Up Alerts
1. Go to: https://console.cloud.google.com/monitoring/alerting
2. Create alert for "Instance count approaching max"
3. Set threshold: 80% of max instances (e.g., 22 out of 28)

---

## Performance Tuning

### Increase Concurrency
If your app can handle more concurrent requests:
```bash
--concurrency 100  # Default is 80
```

### Reduce Min Instances
Save costs by allowing cold starts:
```bash
--min-instances 0  # Scale to zero when idle
```

### Optimize Container
- Reduce image size
- Use multi-stage builds
- Cache dependencies

---

## Current Configuration (Applied)

✅ **Active Configuration:**
```yaml
Memory: 2Gi
CPU: 2
Max Instances: 28
Min Instances: 1
Concurrency: 80
```

This uses your **full CPU quota** (56 vCPUs) and provides:
- **2,240 concurrent requests** maximum
- **Always-on** (min-instances=1, no cold starts)
- **High performance** (2 CPU, 2 GiB per instance)

---

## Recommendations

### For Development/Testing
Use **Option 3** (Cost-Optimized):
- 1 CPU, 1 GiB
- Max 10 instances
- Min 0 instances (scale to zero)

### For Production (Low-Medium Traffic)
Use **Option 2** (Balanced):
- 2 CPU, 2 GiB
- Max 10 instances
- Min 0-1 instances

### For Production (High Traffic)
Use **Option 1** (Maximum Performance):
- 2 CPU, 2 GiB
- Max 28 instances
- Min 1-2 instances

### For Very High Traffic
- Request quota increase to 200+ CPUs
- Or deploy to multiple regions
- Or use **Option 4** (High Concurrency)

---

## Cost Estimates

Based on Cloud Run pricing (as of 2026):

| Configuration | Idle Cost/Month | Active Cost/Month (50% utilization) |
|---------------|-----------------|-------------------------------------|
| Option 1 (28 instances) | $15-20 | $40-60 |
| Option 2 (10 instances) | $5-10 | $15-25 |
| Option 3 (1 CPU, 10 inst) | $3-5 | $8-15 |
| Option 4 (56 instances) | $20-30 | $50-80 |

**Note:** Actual costs depend on:
- Request volume
- Request duration
- Network egress
- Min instances setting

---

## Quick Commands

### Update max instances only
```bash
gcloud run services update civicfix-ai-service \
  --region us-central1 \
  --max-instances 10
```

### Update to cost-optimized
```bash
gcloud run services update civicfix-ai-service \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0
```

### View current configuration
```bash
gcloud run services describe civicfix-ai-service \
  --region us-central1 \
  --format yaml
```

---

**Status**: ✅ FIXED - Max instances set to 28  
**Date**: February 2026  
**Issue**: Quota exceeded (requested 100 instances, allowed 28)  
**Resolution**: Reduced max-instances from 100 to 28
