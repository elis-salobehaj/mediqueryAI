# Backend Dockerfile - Optimized for CI Size & Prod Performance
FROM python:3.12-slim

# Build argument to control which dependencies to install
# Options: 'bedrock', 'local', 'full', 'ci' (default: bedrock for lightweight cloud deployment)
ARG BUILD_MODE=bedrock

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy all requirements files for better caching
COPY requirements*.txt ./

# Use BuildKit cache mount to persist pip cache across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    case "$BUILD_MODE" in \
        bedrock) \
            echo "Bedrock Mode: Installing lightweight cloud dependencies (no heavy ML)"; \
            pip install -r requirements-bedrock.txt; \
            ;; \
        local) \
            echo "Local Mode: Installing dependencies for local models (includes LlamaIndex/HuggingFace)"; \
            pip install -r requirements-local.txt; \
            ;; \
        full) \
            echo "Full Mode: Installing all dependencies"; \
            pip install -r requirements-full.txt; \
            ;; \
        ci) \
            echo "CI Mode: Installing test dependencies without heavy ML"; \
            pip install -r requirements-ci.txt; \
            ;; \
        *) \
            echo "Unknown BUILD_MODE: $BUILD_MODE, defaulting to bedrock"; \
            pip install -r requirements-bedrock.txt; \
            ;; \
    esac

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
