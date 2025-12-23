# Local Model Setup Guide (Ollama)

This guide explains how to set up and use local open-source models with Ollama.

## Quick Start (Docker Only)

We have removed the need for local Ollama installation. The project now runs entirely within Docker with NVIDIA GPU support.

### 1. Prerequisites

- **Docker Desktop** installed
- **NVIDIA Container Toolkit** (for Linux) or proper NVIDIA Drivers (Windows/WSL2)
- **8GB RAM minimum**

### 2. Configure Environment

Edit `backend/.env` (create from `.env.example`):
```bash
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen3:latest
OLLAMA_HOST=http://ollama:11434  # Use the container name 'ollama'
```

### 3. Start Application

```bash
docker compose up -d
```
The Ollama container will automatically pull `qwen3:latest`, `gemma3:4b`, and `qwen2.5:3b` on the first run.

### 4. Verify GPU Usage

```bash
docker compose logs ollama | grep "GPU"
```

## Model Comparison

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| **qwen3:latest** ⭐ | 4.5GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐⭐+ | Coding, Reasoning, SQL (Top Choice) |
| **gemma3:4b** | 2.8GB | 4-6GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | General, Creative, Instruction |
| **qwen2.5:3b** | 2GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Fast Coding |
| **phi3:mini** | 2.3GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | General purpose |


## Switching Between Local and Cloud

### Use Local Model (Free, Private)
```bash
# In backend/.env
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen3:latest

```

### Use Google Gemini API (Higher Quality)
```bash
# In backend/.env
USE_LOCAL_MODEL=false
GEMINI_API_KEY=your_api_key_here
```

## Troubleshooting

### Error: "Connection refused" or "Ollama not found"

**Solution:** Make sure Ollama is running
```bash
# Check if Ollama is running
curl http://localhost:11434

# Start Ollama (if not running)
ollama serve
```

### Error: "Model not found"

**Solution:** Pull the model first
```bash
ollama pull qwen2.5:3b
```

### Slow Performance

**Solutions:**
1. Use a smaller model: `ollama pull gemma2:2b`
2. Reduce context length in `.env`
3. Close other applications to free RAM

### Model Gives Poor Results

**Solutions:**
1. Try a different model: `phi3:mini` or `llama3.2:3b`
2. Switch back to cloud mode: `USE_LOCAL_MODEL=false`
3. Update Ollama: `ollama update`

## Advanced Configuration

### Custom Ollama Host

If running Ollama on a different machine:
```bash
# In backend/.env
OLLAMA_HOST=http://192.168.1.100:11434
```

### GPU Acceleration

Ollama automatically uses GPU if available (NVIDIA, AMD, or Apple Silicon).

Check GPU usage:
```bash
# NVIDIA
nvidia-smi

# AMD
rocm-smi

# macOS
# GPU is used automatically

### Docker GPU Setup (NVIDIA)

1. **Install NVIDIA Container Toolkit**:
   - Follow the [official guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

2. **Enable in docker-compose.yml**:
   - The GPU section is now enabled by default.
   - It reserves 1 NVIDIA GPU for the Ollama container.

3. **Verify**:
   - Run `docker compose up -d`
   - Check logs: `docker compose logs ollama` (look for "detected GPU")
```

## Benefits of Local Models

✅ **Free** - No API costs
✅ **Private** - Data never leaves your machine
✅ **Offline** - Works without internet
✅ **Fast** - No network latency
✅ **Customizable** - Full control over model parameters

## Limitations

❌ **Lower Quality** - Not as good as GPT-4 or Gemini Pro
❌ **Resource Usage** - Requires 4-8GB RAM
❌ **Setup Required** - Need to install Ollama and models

## Recommended Setup

For best results, use **hybrid mode**:
- **Local model** for development and testing (free)
- **Cloud API** for production (higher quality)

Switch between them by changing `USE_LOCAL_MODEL` in `.env`!
