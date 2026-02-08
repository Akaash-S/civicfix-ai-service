#!/bin/bash

# Diagnose gcloud issues

echo "=== gcloud Diagnostics ==="
echo ""

echo "1. gcloud version:"
gcloud version
echo ""

echo "2. Current configuration:"
gcloud config list
echo ""

echo "3. Active account:"
gcloud auth list
echo ""

echo "4. Project info:"
gcloud projects describe asolvitra-skillbridge 2>&1 || echo "Failed to get project info"
echo ""

echo "5. Cloud Run services:"
gcloud run services list --region=us-central1 2>&1 || echo "Failed to list services"
echo ""

echo "6. Secrets:"
gcloud secrets list 2>&1 || echo "Failed to list secrets"
echo ""

echo "7. Running gcloud diagnostics..."
gcloud info --run-diagnostics
echo ""

echo "=== Diagnostics Complete ==="
echo ""
echo "If you see errors above, try:"
echo "1. gcloud auth login"
echo "2. gcloud auth application-default login"
echo "3. gcloud components update"
