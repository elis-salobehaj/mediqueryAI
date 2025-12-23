# Quick Start Script for Docker Deployment (Windows)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  AI Healthcare Data Agent - Docker Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "[OK] Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "[X] Docker is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check if Docker Compose is available
try {
    docker compose version | Out-Null
    Write-Host "[OK] Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "[X] Docker Compose is not available" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Copy environment file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.docker" ".env"
    Write-Host "[OK] .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "[WARNING] Please edit .env and configure:" -ForegroundColor Yellow
    Write-Host "   - USE_LOCAL_MODEL=true (for free local model)" -ForegroundColor White
    Write-Host "   - Or set USE_LOCAL_MODEL=false and add GEMINI_API_KEY or ANTHROPIC_API_KEY for cloud mode" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to continue"
}

# Check if using local model
$useLocal = "false" # Default value
if (Test-Path ".env") {
    $envContent = Get-Content .env | Select-String "USE_LOCAL_MODEL"
    if ($envContent) {
        # Split by comment hash (#), take the first part, then split by =, take the second part, and trim.
        $useLocal = $envContent.ToString().Split('#')[0].Split('=')[1].Trim()
    }
}

Write-Host "Starting Docker services..." -ForegroundColor Yellow
Write-Host ""

if ($useLocal -eq "true") {
    Write-Host "[LOCAL] Local model mode detected - starting with Ollama..." -ForegroundColor Cyan
    docker compose --profile local-model up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Failed to start Docker services" -ForegroundColor Red
        exit 1
    }
    switch ($LASTEXITCODE) {
        0 { 
            Write-Host "[OK] Containers started successfully" -ForegroundColor Green
            Write-Host "Note: Ollama is pulling models in the background. This may take a few minutes." -ForegroundColor Yellow
        }
        default { 
            Write-Host "[X] Failed to start containers." -ForegroundColor Red
        }
    }
} else {
    Write-Host "[CLOUD] Cloud mode detected - starting without Ollama..." -ForegroundColor Cyan
    docker compose up -d
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:3000 (Container: mediquery-ai-frontend)" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000 (Container: mediquery-ai-backend)" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
if ($useLocal -eq "true") {
    Write-Host "  Ollama:    http://localhost:11434 (Container: mediquery-ai-ollama)" -ForegroundColor White
}
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  docker compose logs -f          # View logs" -ForegroundColor White
Write-Host "  docker compose ps               # Check status" -ForegroundColor White
Write-Host "  docker compose down             # Stop all services" -ForegroundColor White
Write-Host "  docker compose restart backend  # Restart backend" -ForegroundColor White
Write-Host ""
Write-Host "Happy querying!" -ForegroundColor Green
