
Write-Host "=========================================="
Write-Host "   RUNNING MEDIQUERY AI TEST SUITE"
Write-Host "=========================================="
Write-Host ""

Write-Host "[1/2] Running Backend Tests (Pytest)..." -ForegroundColor Cyan
try {
    docker compose -f docker-compose.test.yml run --rm backend-test
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend Tests Passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend Tests Failed!" -ForegroundColor Red
    }
} catch {
    Write-Host "Error running backend tests: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/2] Running Frontend Tests (Playwright)..." -ForegroundColor Cyan
Write-Host "Note: First run will take time to install dependencies inside the container." -ForegroundColor Yellow

try {
    docker compose -f docker-compose.test.yml run --rm frontend-test-ct
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend Tests Passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend Tests Failed!" -ForegroundColor Red
    }
} catch {
    Write-Host "Error running frontend tests: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Test execution complete."
