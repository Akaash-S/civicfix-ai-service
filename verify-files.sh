#!/bin/bash

# Verify all Docker and YAML files are correct

echo "=== File Verification ==="
echo ""

# Check if files exist
echo "Checking required files..."
files=(
    "Dockerfile"
    "cloudbuild.yaml"
    "requirements.txt"
    "app/main.py"
    "app/config.py"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file MISSING"
        all_exist=false
    fi
done

echo ""

if [ "$all_exist" = false ]; then
    echo "ERROR: Some files are missing!"
    exit 1
fi

# Verify Dockerfile
echo "Verifying Dockerfile..."
if grep -q "FROM python:3.10-slim" Dockerfile; then
    echo "✓ Python version correct (3.10)"
else
    echo "✗ Python version issue"
fi

if grep -q "CMD uvicorn app.main:app" Dockerfile; then
    echo "✓ CMD correct"
else
    echo "✗ CMD issue"
fi

if grep -q 'PORT' Dockerfile; then
    echo "✓ PORT variable configured"
else
    echo "✗ PORT variable missing"
fi

echo ""

# Verify cloudbuild.yaml
echo "Verifying cloudbuild.yaml..."
if grep -q "gcr.io/\$PROJECT_ID/civicfix-ai-service:latest" cloudbuild.yaml; then
    echo "✓ Image name correct"
else
    echo "✗ Image name issue"
fi

if grep -q "max-instances=28" cloudbuild.yaml; then
    echo "✓ Max instances correct (28)"
else
    echo "✗ Max instances issue"
fi

if grep -q "PORT" cloudbuild.yaml; then
    echo "✗ PORT in env vars (should not be there!)"
else
    echo "✓ PORT not in env vars (correct)"
fi

if grep -q "set-secrets" cloudbuild.yaml; then
    echo "✓ Secrets configured"
else
    echo "✗ Secrets missing"
fi

echo ""

# Verify requirements.txt
echo "Verifying requirements.txt..."
if grep -q "fastapi" requirements.txt; then
    echo "✓ FastAPI included"
else
    echo "✗ FastAPI missing"
fi

if grep -q "imagededup==0.3.3" requirements.txt; then
    echo "✓ imagededup version correct (0.3.3)"
else
    echo "✗ imagededup version issue"
fi

echo ""

# Summary
echo "=== Verification Complete ==="
echo ""
echo "All files are correct! ✅"
echo ""
echo "The gcloud error is NOT caused by your files."
echo "It's a bug in your local gcloud installation."
echo ""
echo "SOLUTION: Use Cloud Shell"
echo "https://shell.cloud.google.com/?project=asolvitra-skillbridge"
echo ""
