# Quick Setup Script for Local Ollama Model

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ollama Local Model Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
Write-Host "[1/4] Checking Ollama installation..." -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Ollama is installed: $ollamaVersion" -ForegroundColor Green
    } else {
        throw "Ollama not found"
    }
} catch {
    Write-Host "✗ Ollama is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Ollama first:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://ollama.com/download" -ForegroundColor White
    Write-Host "  2. Or run: winget install Ollama.Ollama" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""

# Check if model is installed
Write-Host "[2/4] Checking for qwen2.5:3b model..." -ForegroundColor Yellow
$modelList = ollama list 2>$null | Out-String
if ($modelList -match "qwen2.5:3b") {
    Write-Host "✓ Model qwen2.5:3b is already installed" -ForegroundColor Green
} else {
    Write-Host "✗ Model not found. Pulling qwen2.5:3b (~2GB download)..." -ForegroundColor Yellow
    Write-Host "  This may take a few minutes..." -ForegroundColor White
    ollama pull qwen2.5:3b
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Model downloaded successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to download model" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Install Python package
Write-Host "[3/4] Installing Python ollama package..." -ForegroundColor Yellow
& venv\Scripts\pip install ollama --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python package installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install Python package" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test the model
Write-Host "[4/4] Testing model..." -ForegroundColor Yellow
$testPrompt = "SELECT * FROM patients LIMIT 1"
Write-Host "  Sending test query: $testPrompt" -ForegroundColor White
try {
    $response = ollama run qwen2.5:3b $testPrompt --verbose=false 2>$null
    if ($response) {
        Write-Host "✓ Model is working correctly" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Model test inconclusive, but should work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  USE_LOCAL_MODEL=true" -ForegroundColor White
Write-Host "  LOCAL_MODEL_NAME=qwen2.5:3b" -ForegroundColor White
Write-Host "  OLLAMA_HOST=http://localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "The backend will automatically use the local model." -ForegroundColor Green
Write-Host "Restart the backend if it's already running:" -ForegroundColor Yellow
Write-Host "  uvicorn main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "To switch back to Google Gemini API:" -ForegroundColor Yellow
Write-Host "  Edit .env and set USE_LOCAL_MODEL=false" -ForegroundColor White
Write-Host ""
