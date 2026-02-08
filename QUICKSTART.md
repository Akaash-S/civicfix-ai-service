# CivicFix AI Verification Service - Quick Start Guide

## Prerequisites

- Python 3.11+
- PostgreSQL database (Neon or local)
- Docker (optional)

## Installation

### Option 1: Local Development

1. **Create virtual environment**
   ```bash
   cd ai-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Required variables:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/civicfix
   API_KEY=your_secure_api_key_here
   SECRET_KEY=your_secret_key_here
   ENABLE_MOCK_AI=true
   ```

4. **Run database migrations**
   ```bash
   # From the backend directory
   cd ../backend
   psql $DATABASE_URL < migrations/add_ai_verification_tables.sql
   ```

5. **Start the service**
   ```bash
   cd ../ai-service
   uvicorn app.main:app --reload --port 8001
   ```

6. **Test the service**
   ```bash
   curl http://localhost:8001/health
   ```

### Option 2: Docker

1. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and run**
   ```bash
   docker-compose up --build
   ```

3. **Test the service**
   ```bash
   curl http://localhost:8001/health
   ```

## Usage Examples

### 1. Verify Initial Issue

```bash
curl -X POST http://localhost:8001/api/v1/verify/initial \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "issue_id": 123,
    "image_urls": [
      "https://storage.example.com/image1.jpg"
    ],
    "category": "Road Infrastructure",
    "location": {
      "latitude": 13.0827,
      "longitude": 80.2707
    },
    "description": "Large pothole on main road"
  }'
```

Expected response:
```json
{
  "issue_id": 123,
  "status": "APPROVED",
  "confidence_score": 0.92,
  "checks": {
    "fake_detection": {
      "status": "PASSED",
      "confidence": 0.95,
      "details": "Image appears to be authentic"
    },
    "duplicate_detection": {
      "status": "PASSED",
      "confidence": 0.95,
      "details": "No duplicate detected"
    },
    "metadata_validation": {
      "status": "WARNING",
      "confidence": 0.85,
      "details": "No GPS data in EXIF"
    },
    "location_consistency": {
      "status": "WARNING",
      "confidence": 0.7,
      "details": "No GPS data in image metadata"
    },
    "category_relevance": {
      "status": "PASSED",
      "confidence": 0.88,
      "details": "Category 'Road Infrastructure' appears relevant"
    }
  },
  "rejection_reasons": [],
  "warnings": [
    "No GPS data in EXIF",
    "No GPS data in image metadata"
  ],
  "processing_time_ms": 2341,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Cross-Verify Resolution

```bash
curl -X POST http://localhost:8001/api/v1/verify/cross-check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "issue_id": 123,
    "citizen_images": [
      "https://storage.example.com/before.jpg"
    ],
    "government_images": [
      "https://storage.example.com/after.jpg"
    ],
    "location": {
      "latitude": 13.0827,
      "longitude": 80.2707
    },
    "issue_category": "Road Infrastructure"
  }'
```

Expected response:
```json
{
  "issue_id": 123,
  "status": "APPROVED",
  "confidence_score": 0.88,
  "same_location": true,
  "work_completed": true,
  "image_similarity_score": 0.65,
  "notes": "✓ Location verified (distance: 15.3m) | Image similarity: 65.00% | ✓ Visual changes detected - work appears completed | Category: Road Infrastructure",
  "warnings": [],
  "processing_time_ms": 1823,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 3. Get Verification Status

```bash
curl http://localhost:8001/api/v1/verify/status/123 \
  -H "X-API-Key: your_api_key_here"
```

### 4. Get Statistics

```bash
curl http://localhost:8001/api/v1/stats \
  -H "X-API-Key: your_api_key_here"
```

## Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Integration with Backend

### Update Backend to Call AI Service

In `backend/app.py`, add AI verification call after issue creation:

```python
import httpx

AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://localhost:8001')
AI_SERVICE_API_KEY = os.environ.get('AI_SERVICE_API_KEY')

async def verify_issue_with_ai(issue_id, image_urls, category, location, description):
    """Call AI service to verify issue"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/api/v1/verify/initial",
                json={
                    "issue_id": issue_id,
                    "image_urls": image_urls,
                    "category": category,
                    "location": {
                        "latitude": location['latitude'],
                        "longitude": location['longitude']
                    },
                    "description": description
                },
                headers={"X-API-Key": AI_SERVICE_API_KEY},
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"AI verification failed: {e}")
        return None
```

## Configuration

### Confidence Thresholds

Adjust in `.env`:
```env
MIN_CONFIDENCE_SCORE=0.7
AUTO_APPROVE_THRESHOLD=0.9
AUTO_REJECT_THRESHOLD=0.3
```

### Enable/Disable Checks

```env
FAKE_DETECTION_ENABLED=true
DUPLICATE_DETECTION_ENABLED=true
LOCATION_VALIDATION_ENABLED=true
CATEGORY_VALIDATION_ENABLED=true
```

### Mock AI Mode

For development without real AI models:
```env
ENABLE_MOCK_AI=true
```

## Monitoring

- **Health Check**: `GET /health`
- **Statistics**: `GET /api/v1/stats`
- **Logs**: Check console output or configure log file

## Troubleshooting

### Service won't start
- Check DATABASE_URL is correct
- Ensure PostgreSQL is running
- Verify all required environment variables are set

### Verification fails
- Check image URLs are accessible
- Verify API key is correct
- Check logs for detailed error messages

### Low confidence scores
- Adjust thresholds in configuration
- Enable/disable specific checks
- Review check details in response

## Next Steps

1. **Integrate with Backend**: Add AI verification calls to issue creation endpoint
2. **Add Real AI Models**: Replace mock detection with actual ML models
3. **Set up Monitoring**: Configure Prometheus/Grafana for metrics
4. **Deploy to Production**: Use Docker/Kubernetes for deployment
5. **Enable Advanced Features**: Internet search, advanced analysis

## Support

For issues and questions:
- Check logs: `docker-compose logs -f ai-service`
- Review documentation: `README.md`
- Contact: support@civicfix.com
