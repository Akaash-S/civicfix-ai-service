#!/bin/bash

# Automated Test Runner for CivicFix AI Service

set -e

echo "=========================================="
echo "  CivicFix AI Service - Test Runner"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check if port 8080 is available
if netstat -an 2>/dev/null | grep -q ":8080.*LISTEN" || lsof -i :8080 > /dev/null 2>&1; then
    echo "⚠ Port 8080 is already in use"
    echo "  Stop the service using that port or change the port in docker-compose.yml"
    exit 1
fi

echo "✓ Port 8080 is available"
echo ""

# Build and start service
echo "Building and starting service..."
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo "✗ Failed to start service"
    exit 1
fi

echo "✓ Service started"
echo ""

# Wait for service to be ready
echo "Waiting for service to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✓ Service is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo "✗ Service did not start in time"
        echo ""
        echo "Logs:"
        docker-compose logs
        docker-compose down
        exit 1
    fi
    
    sleep 1
done

echo ""

# Run tests
echo "Running tests..."
echo ""

python test_local.py
test_result=$?

echo ""

# Stop service
echo "Stopping service..."
docker-compose down

echo ""

# Exit with test result
if [ $test_result -eq 0 ]; then
    echo "=========================================="
    echo "  ✓ All tests passed!"
    echo "=========================================="
    echo ""
    echo "Your service is ready to deploy!"
    echo "Run: gcloud builds submit --config cloudbuild.yaml"
    exit 0
else
    echo "=========================================="
    echo "  ✗ Tests failed"
    echo "=========================================="
    echo ""
    echo "Fix the issues above before deploying."
    exit 1
fi
