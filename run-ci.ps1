Write-Host "=========================================="
Write-Host "   RUNNING MEDIQUERY AI - CI SUITE"
Write-Host "   (Unit & Component Tests - Isolated)"
Write-Host "=========================================="
Write-Host ""

# 1. Backend Unit
Write-Host "[1/2] Backend Unit Tests..." -ForegroundColor Cyan
docker compose -f docker-compose.test.yml run --rm backend-unit
$BackendExit = $LASTEXITCODE

# 2. Frontend Component
Write-Host ""
Write-Host "[2/2] Frontend Component Tests..." -ForegroundColor Cyan
Write-Host "Note: First run will take time to install dependencies inside the container if not cached" -ForegroundColor Yellow
docker compose -f docker-compose.test.yml run --rm frontend-component
$FrontendExit = $LASTEXITCODE

Write-Host ""
if ($BackendExit -eq 0 -and $FrontendExit -eq 0) {
    Write-Host "✅ All CI Tests Passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some CI Tests Failed!" -ForegroundColor Red
    exit 1
}
