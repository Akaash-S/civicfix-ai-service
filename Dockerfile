# CivicFix AI Verification Service - Dockerfile

FROM python:3.10-slim

# Set environment variables to avoid debconf warnings
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip and install Python dependencies with retry logic
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt || \
    (sleep 5 && pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt) || \
    (sleep 10 && pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt)

# Copy application code
COPY app/ ./app/

# Create models directory
RUN mkdir -p models

# Expose port (Cloud Run will set PORT env variable at runtime)
ENV PORT=8080
EXPOSE 8080

# Note: Health check removed - Cloud Run has its own health checking
# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
