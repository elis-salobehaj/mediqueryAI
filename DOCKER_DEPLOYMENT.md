# Docker Deployment Guide

Complete guide for running the AI Healthcare Data Agent with Docker Compose.

## Quick Start

### 1. Prerequisites

- **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
- **Docker Compose** (included with Docker Desktop)
- **8GB RAM minimum** (for Ollama model)

### 2. Setup Environment

```bash
# Copy environment template
cp .env.docker .env

# Edit .env with your settings
# For local model (free): USE_LOCAL_MODEL=true
# For cloud API: USE_LOCAL_MODEL=false and add GEMINI_API_KEY
```

### 3. Start All Services

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Pull Ollama Model (First Time Only)

```bash
# Pull the Qwen2.5 model (~2GB)
docker exec -it antigravity-ollama ollama pull qwen2.5:3b

# Verify model is installed
docker exec -it antigravity-ollama ollama list
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

---

## Services Overview

### 🤖 Ollama (Local LLM)
- **Container**: `antigravity-ollama`
- **Port**: 11434
- **Volume**: `ollama_data` (persists models)
- **Model**: qwen2.5:3b (2GB)

### 🔧 Backend (FastAPI)
- **Container**: `antigravity-backend`
- **Port**: 8000
- **Volumes**: 
  - `./backend` → `/app` (code)
  - `./backend/data` → `/app/data` (CSV files)

### 🎨 Frontend (React + Nginx)
- **Container**: `antigravity-frontend`
- **Port**: 3000
- **Built with**: Multi-stage Docker build

---

## Common Commands

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend
docker-compose logs -f ollama
```

### Manage Ollama Models

```bash
# List installed models
docker exec -it antigravity-ollama ollama list

# Pull a different model
docker exec -it antigravity-ollama ollama pull phi3:mini

# Remove a model
docker exec -it antigravity-ollama ollama rm qwen2.5:3b

# Test model
docker exec -it antigravity-ollama ollama run qwen2.5:3b "SELECT * FROM patients LIMIT 1"
```

### Development Mode

```bash
# Backend hot-reload (already configured)
# Edit files in ./backend and changes auto-reload

# Frontend rebuild
docker-compose build frontend
docker-compose up -d frontend

# View backend logs
docker-compose logs -f backend
```

### Database & Data

```bash
# Access backend container
docker exec -it antigravity-backend bash

# View chat history database
docker exec -it antigravity-backend ls -lh chat_history.db

# Backup data
docker cp antigravity-backend:/app/chat_history.db ./backup/
docker cp antigravity-backend:/app/data ./backup/
```

---

## Configuration

### Environment Variables (.env)

```bash
# Required for cloud mode
GEMINI_API_KEY=your_api_key_here

# Chat history retention (hours)
CHAT_HISTORY_RETENTION_HOURS=24

# Local model settings
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen2.5:3b
```

### Switch Between Local and Cloud

**Use Local Ollama (Free):**
```bash
# In .env
USE_LOCAL_MODEL=true

# Restart backend
docker-compose restart backend
```

**Use Google Gemini (Cloud):**
```bash
# In .env
USE_LOCAL_MODEL=false
GEMINI_API_KEY=your_actual_key

# Restart backend
docker-compose restart backend
```

---

## GPU Support (Optional)

For faster Ollama inference with NVIDIA GPU:

### 1. Install NVIDIA Container Toolkit

```bash
# Ubuntu/Linux
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Uncomment GPU Section in docker-compose.yml

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### 3. Restart Services

```bash
docker-compose down
docker-compose up -d
```

---

## Troubleshooting

### Ollama Model Not Found

```bash
# Pull the model
docker exec -it antigravity-ollama ollama pull qwen2.5:3b

# Check if it's installed
docker exec -it antigravity-ollama ollama list
```

### Backend Can't Connect to Ollama

```bash
# Check if Ollama is running
docker-compose ps ollama

# Check Ollama health
docker exec -it antigravity-ollama curl http://localhost:11434/api/tags

# Restart services in order
docker-compose restart ollama
docker-compose restart backend
```

### Frontend Not Loading

```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check logs
docker-compose logs frontend
```

### Port Already in Use

```bash
# Change ports in docker-compose.yml
ports:
  - "3001:80"  # Frontend (was 3000)
  - "8001:8000"  # Backend (was 8000)
```

### Out of Memory

```bash
# Use a smaller model
docker exec -it antigravity-ollama ollama pull gemma2:2b

# Update .env
LOCAL_MODEL_NAME=gemma2:2b

# Restart backend
docker-compose restart backend
```

---

## Production Deployment

### 1. Build Optimized Images

```bash
# Build without cache
docker-compose build --no-cache

# Use production .env
cp .env.production .env
```

### 2. Security Hardening

```bash
# Use secrets for API keys (Docker Swarm/Kubernetes)
# Enable HTTPS with reverse proxy (nginx/traefik)
# Set resource limits in docker-compose.yml
```

### 3. Resource Limits

Add to docker-compose.yml:

```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4'
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
```

---

## Backup & Restore

### Backup

```bash
# Create backup directory
mkdir -p backup

# Backup volumes
docker run --rm -v ollama_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/ollama_data.tar.gz -C /data .

# Backup database
docker cp antigravity-backend:/app/chat_history.db ./backup/

# Backup CSV data
docker cp antigravity-backend:/app/data ./backup/
```

### Restore

```bash
# Restore Ollama data
docker run --rm -v ollama_data:/data -v $(pwd)/backup:/backup alpine tar xzf /backup/ollama_data.tar.gz -C /data

# Restore database
docker cp ./backup/chat_history.db antigravity-backend:/app/

# Restart services
docker-compose restart
```

---

## Monitoring

### View Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats antigravity-ollama
```

### Health Checks

```bash
# Check all services
docker-compose ps

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
curl http://localhost:3000
```

---

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker system prune -a --volumes
```

---

## Benefits of Docker Deployment

✅ **Isolated Environment** - No conflicts with system packages
✅ **Easy Setup** - One command to start everything
✅ **Consistent** - Works the same on any OS
✅ **Portable** - Easy to deploy anywhere
✅ **Scalable** - Can add more services easily
✅ **Version Control** - Infrastructure as code

---

## Next Steps

1. ✅ Start services: `docker-compose up -d`
2. ✅ Pull model: `docker exec -it antigravity-ollama ollama pull qwen2.5:3b`
3. ✅ Access app: http://localhost:3000
4. ✅ Test queries and visualizations
5. ✅ Monitor logs: `docker-compose logs -f`

**Your AI Healthcare Data Agent is now running in Docker!** 🚀
