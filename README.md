# CivicFix AI Verification Service

## Overview

This microservice handles all AI-driven verification tasks for the CivicFix platform:

- **Fake/AI-Generated Image Detection**
- **Duplicate Image Detection**
- **Internet Image Reuse Check**
- **Metadata & Location Consistency Validation**
- **Issue-Category Relevance Check**
- **Cross-Verification** (Citizen vs Government Images)

## Architecture

```
ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models.py               # Pydantic models
│   ├── database.py             # Database connection
│   └── services/
│       ├── __init__.py
│       ├── fake_detection.py   # AI-generated image detection
│       ├── duplicate_detection.py  # Duplicate image finder
│       ├── metadata_validator.py   # EXIF/metadata validation
│       ├── location_validator.py   # GPS consistency check
│       ├── category_validator.py   # Issue-category relevance
│       ├── cross_verification.py   # Compare before/after images
│       └── internet_search.py      # Reverse image search
├── tests/
│   ├── __init__.py
│   └── test_services.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Features

### 1. Fake/AI-Generated Image Detection
- Uses deep learning models to detect AI-generated images
- Checks for common AI artifacts
- Analyzes image patterns and inconsistencies

### 2. Duplicate Image Detection
- Perceptual hashing (pHash)
- Feature extraction and comparison
- Database of known images

### 3. Internet Image Reuse Check
- Reverse image search integration
- Checks against public image databases
- Detects stock photos and reused content

### 4. Metadata Validation
- EXIF data extraction
- GPS coordinates validation
- Timestamp consistency check
- Camera information verification

### 5. Location Consistency
- Compare EXIF GPS with reported location
- Validate proximity (within acceptable radius)
- Flag suspicious location mismatches

### 6. Category Relevance
- NLP-based image classification
- Match image content with issue category
- Confidence scoring

### 7. Cross-Verification
- Compare citizen "before" images with government "after" images
- Validate same location
- Detect actual work completion
- Flag fake resolutions

## API Endpoints

### Verification Endpoints

```
POST /api/v1/verify/initial
- Verify newly submitted issue
- Returns: approval/rejection with reasons

POST /api/v1/verify/cross-check
- Compare citizen vs government images
- Returns: verification result

GET /api/v1/verify/status/{issue_id}
- Get verification status
- Returns: current verification state

POST /api/v1/verify/revalidate/{issue_id}
- Re-run verification on existing issue
- Returns: updated verification result
```

### Health & Monitoring

```
GET /health
- Service health check

GET /metrics
- Prometheus metrics

GET /api/v1/stats
- Verification statistics
```

## Installation

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8001
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t civicfix-ai-service .
docker run -p 8001:8001 civicfix-ai-service
```

## Configuration

Environment variables (`.env`):

```env
# Service Configuration
SERVICE_NAME=civicfix-ai-service
SERVICE_PORT=8001
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/civicfix

# AI Models
FAKE_DETECTION_MODEL=path/to/model
DUPLICATE_THRESHOLD=0.85
LOCATION_RADIUS_METERS=100

# External APIs
GOOGLE_VISION_API_KEY=your_key_here
REVERSE_IMAGE_SEARCH_API_KEY=your_key_here

# Confidence Thresholds
MIN_CONFIDENCE_SCORE=0.7
AUTO_APPROVE_THRESHOLD=0.9
AUTO_REJECT_THRESHOLD=0.3
```

## Usage Examples

### Verify Initial Issue

```python
import requests

response = requests.post(
    "http://localhost:8001/api/v1/verify/initial",
    json={
        "issue_id": 123,
        "image_urls": [
            "https://storage.example.com/image1.jpg",
            "https://storage.example.com/image2.jpg"
        ],
        "category": "Road Infrastructure",
        "location": {
            "latitude": 13.0827,
            "longitude": 80.2707
        },
        "description": "Large pothole on main road"
    }
)

result = response.json()
# {
#   "status": "APPROVED",
#   "confidence_score": 0.92,
#   "checks": {
#     "fake_detection": "PASSED",
#     "duplicate_detection": "PASSED",
#     "metadata_validation": "PASSED",
#     "location_consistency": "PASSED",
#     "category_relevance": "PASSED"
#   },
#   "rejection_reasons": []
# }
```

### Cross-Verification

```python
response = requests.post(
    "http://localhost:8001/api/v1/verify/cross-check",
    json={
        "issue_id": 123,
        "citizen_images": [
            "https://storage.example.com/before1.jpg"
        ],
        "government_images": [
            "https://storage.example.com/after1.jpg"
        ],
        "location": {
            "latitude": 13.0827,
            "longitude": 80.2707
        }
    }
)

result = response.json()
# {
#   "status": "VERIFIED_SOLVED",
#   "confidence_score": 0.88,
#   "same_location": true,
#   "work_completed": true,
#   "notes": "Road repair verified. Surface appears fixed."
# }
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_services.py::test_fake_detection
```

## Deployment

### Production Deployment

1. **Build Docker image**
   ```bash
   docker build -t civicfix-ai-service:latest .
   ```

2. **Push to registry**
   ```bash
   docker tag civicfix-ai-service:latest registry.example.com/civicfix-ai-service:latest
   docker push registry.example.com/civicfix-ai-service:latest
   ```

3. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

### Scaling

The service is stateless and can be horizontally scaled:

```bash
docker-compose up --scale ai-service=3
```

## Monitoring

- **Prometheus metrics** available at `/metrics`
- **Health checks** at `/health`
- **Logs** structured JSON format

## Security

- API key authentication required
- Rate limiting enabled
- Input validation on all endpoints
- Secure image download and processing
- No permanent storage of images

## Performance

- Average verification time: 2-5 seconds per issue
- Concurrent processing: Up to 10 requests
- Image processing: Optimized with caching
- Database queries: Indexed and optimized

## Roadmap

- [ ] Real AI model integration (currently using mock/heuristics)
- [ ] Advanced deep learning models for fake detection
- [ ] Blockchain integration for immutable verification logs
- [ ] Multi-language support for NLP
- [ ] Real-time verification streaming
- [ ] Advanced anomaly detection

## License

Proprietary - CivicFix Platform

## Support

For issues and questions, contact: support@civicfix.com
