# Local Model Setup Guide (Ollama)

This guide explains how to set up and use local open-source models with Ollama.

## Quick Start

### 1. Install Ollama

**Windows:**
```powershell
# Download and install from: https://ollama.com/download
# Or use winget:
winget install Ollama.Ollama
```

**Ubuntu/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

### 2. Pull the Model

```bash
# Pull Qwen2.5 3B (recommended - 2GB)
ollama pull qwen2.5:3b

# Or try other models:
ollama pull phi3:mini        # Phi-3 Mini (3.8B - 2.3GB)
ollama pull llama3.2:3b      # Llama 3.2 (3B - 2GB)
ollama pull gemma2:2b        # Gemma 2 (2B - 1.4GB)
```

### 3. Verify Installation

```bash
# List installed models
ollama list

# Test the model
ollama run qwen2.5:3b
>>> Hello, how are you?
```

### 4. Configure the Application

Edit `backend/.env`:
```bash
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen2.5:3b
OLLAMA_HOST=http://localhost:11434
```

### 5. Install Python Dependencies

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install ollama
```

### 6. Restart the Backend

```bash
# The backend will auto-reload if already running
# Or restart manually:
uvicorn main:app --reload
```

## Model Comparison

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| **qwen2.5:3b** ⭐ | 2GB | 4-8GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Coding, SQL, reasoning |
| **phi3:mini** | 2.3GB | 4-8GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | General purpose |
| **llama3.2:3b** | 2GB | 4-8GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Instruction following |
| **gemma2:2b** | 1.4GB | 3-6GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Lightweight tasks |

## Switching Between Local and Cloud

### Use Local Model (Free, Private)
```bash
# In backend/.env
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen2.5:3b
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
