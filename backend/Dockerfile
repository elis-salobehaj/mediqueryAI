# Backend Dockerfile - Optimized for CI Size & Prod Performance
FROM python:3.12-slim

# Build argument to control cleanup mode: 'ci' or 'production' (default)
ARG BUILD_MODE=production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-ci.txt .

# Use BuildKit cache mount to persist pip cache across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$BUILD_MODE" = "ci" ]; then \
        echo "CI Mode: Installing lightweight dependencies (no heavy ML/PyTorch)"; \
        pip install -r requirements-ci.txt; \
    else \
        echo "Production Mode: Installing full dependencies (with LlamaIndex/PyTorch)"; \
        pip install -r requirements.txt; \
    fi

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
