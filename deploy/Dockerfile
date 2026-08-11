# Dockerfile for Linelist Cleaner & Spatial Cascade Server
FROM python:3.11-slim

LABEL maintainer="pratisig"
LABEL description="Linelist Cleaner & Spatial Fallback Cascade (OCHA COD-AB) Web Application"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["python3", "-m", "linelist_cleaner.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
