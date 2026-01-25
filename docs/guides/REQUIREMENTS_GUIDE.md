# Backend Requirements Structure

## Overview

The backend dependencies are now organized into modular files to prevent unnecessary heavy library installations based on deployment mode.

## Files

### Core Requirements

- **`requirements-base.txt`** - Core dependencies needed for all configurations
  - FastAPI, SQLAlchemy, pandas, authentication
  - LangGraph multi-agent framework
  - AWS Bedrock support (boto3, langchain-aws)
  
### Feature-Specific Requirements

- **`requirements-bedrock.txt`** - Lightweight Bedrock-only deployment
  - Extends: `requirements-base.txt`
  - Size: ~300MB installed
  - Use when: `USE_BEDROCK=true` in production
  - No PyTorch, no HuggingFace transformers
  
- **`requirements-local.txt`** - Local model support (Ollama + semantic search)
  - Extends: `requirements-base.txt`
  - Size: ~3-5GB installed (includes PyTorch, HuggingFace)
  - Use when: `USE_LOCAL_MODEL=true` or semantic search needed
  - Includes: LlamaIndex, HuggingFace embeddings
  
- **`requirements-full.txt`** - All features enabled
  - Combines: base + local + bedrock
  - Size: ~5GB installed
  - Use when: Supporting multiple deployment modes

### Testing & CI

- **`requirements-test.txt`** - Testing without heavy ML
  - Extends: `requirements-base.txt`
  - Adds: pytest, pytest-asyncio
  - Mocks heavy libraries in `conftest.py`
  
- **`requirements-ci.txt`** - CI/CD pipeline dependencies
  - Extends: `requirements-test.txt`
  - Includes lightweight API clients for integration testing
  - No PyTorch or ML model downloads

- **`requirements.txt`** - Legacy compatibility
  - Points to `requirements-full.txt`
  - For backward compatibility

## Usage

### Local Development

```bash
# Bedrock-only (lightweight, recommended for cloud)
pip install -r requirements-bedrock.txt

# Local models with semantic search
pip install -r requirements-local.txt

# Everything (useful for development across modes)
pip install -r requirements-full.txt
```

### Docker Build

```bash
# Bedrock deployment (default, ~300MB)
docker build --build-arg BUILD_MODE=bedrock -t mediqueryai-backend .

# Local models deployment (~5GB)
docker build --build-arg BUILD_MODE=local -t mediqueryai-backend .

# Full features
docker build --build-arg BUILD_MODE=full -t mediqueryai-backend .

# CI testing
docker build --build-arg BUILD_MODE=ci -t mediqueryai-backend .
```

### Docker Compose

Update [docker-compose.yml](../docker-compose.yml) build args:

```yaml
services:
  backend:
    build:
      context: ./backend
      args:
        BUILD_MODE: bedrock  # or 'local', 'full', 'ci'
```

## Environment Variables

Set in [.env](../.env) file:

```bash
# For Bedrock deployment (lightweight)
USE_BEDROCK=true
USE_LOCAL_MODEL=false

# For local model deployment (heavy)
USE_BEDROCK=false
USE_LOCAL_MODEL=true

# Hybrid mode (requires requirements-full.txt)
USE_BEDROCK=true
USE_LOCAL_MODEL=true
```

## Migration from Old Structure

### Before
- `requirements.txt` - Everything included (~5GB)
- `requirements-ci.txt` - Duplicated all dependencies
- `requirements-test.txt` - Duplicated most dependencies

### After
- Modular structure with `-r` references
- No duplication
- Conditional installation based on features
- 5x faster Bedrock deployments (no PyTorch download)

## Troubleshooting

### Issue: "Module not found" errors

**Cause**: Installed wrong requirements file for your USE_BEDROCK/USE_LOCAL_MODEL setting

**Solution**:
- `USE_BEDROCK=true` → Install `requirements-bedrock.txt`
- `USE_LOCAL_MODEL=true` → Install `requirements-local.txt`
- Both enabled → Install `requirements-full.txt`

### Issue: Still downloading PyTorch with USE_BEDROCK=true

**Check**: 
1. Verify you installed `requirements-bedrock.txt` not `requirements.txt`
2. Check `pip list | grep torch` - should be empty
3. Rebuild Docker with `--no-cache` and `BUILD_MODE=bedrock`

### Issue: Import errors in llm_agent.py

The code has conditional imports with try/except blocks. If libraries aren't installed:
- `HAS_BEDROCK = False` when langchain-aws missing
- `HAS_LLAMA_INDEX = False` when llama-index missing

These flags control feature availability at runtime.

## Benefits

1. **Faster Bedrock Deployments**: 5x faster, 90% less disk space
2. **Cost Savings**: Reduced container size = lower storage/bandwidth costs
3. **Cleaner Dependencies**: No circular dependencies or duplicates
4. **Explicit Feature Control**: Clear relationship between requirements and features
5. **Better Testing**: CI doesn't download unnecessary ML models
