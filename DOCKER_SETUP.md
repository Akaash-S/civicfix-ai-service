# Docker Setup - CivicFix AI Service

## Single Dockerfile Configuration

This project uses a **single Dockerfile** for all environments (development, staging, production) to avoid confusion.

### Files:
- ✅ `Dockerfile` - Main and only Docker configuration
- ✅ `docker-compose.yml` - Local development setup
- ✅ `cloudbuild.yaml` - GCP Cloud Build configuration
- ❌ `Dockerfile.production` - REMOVED (no longer needed)

## Port Configuration

The service uses **port 8080** for consistency with Cloud Run:
- **Local development**: Access at `http://localhost:8001` (mapped from container port 8080)
- **Cloud Run**: Automatically uses port 8080 via `PORT` environment variable

## Usage

### Local Development
```bash
docker-compose up
```
Access at: http://localhost:8001

### GCP Deployment
```bash
./deploy-to-gcp.sh
```

### Manual Docker Build
```bash
docker build -t civicfix-ai-service .
docker run -p 8001:8080 -e PORT=8080 civicfix-ai-service
```

## Environment Variables

Key variables in the Dockerfile:
- `PORT=8080` - Service port (configurable)
- Set via docker-compose.yml or Cloud Run deployment

## Notes

- The Dockerfile is optimized for both development and production
- Health checks are configured for port 8080
- All deployment scripts reference the single `Dockerfile`
