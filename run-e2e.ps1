Write-Host "=========================================="
Write-Host "   RUNNING MEDIQUERY AI - E2E SUITE"
Write-Host "   (Full Stack Integration Tests)"
Write-Host "=========================================="
Write-Host ""

Write-Host "[E2E] Starting Full Stack Environment..." -ForegroundColor Cyan
# Clean up previous runs
docker compose -f docker-compose.test.yml down -v

Write-Host "[E2E] Building and Running Tests..." -ForegroundColor Cyan
# Abort entire stack if the runner fails (exit-code-from implies abort-on-container-exit)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from e2e-runner backend frontend e2e-runner
$ExitCode = $LASTEXITCODE

Write-Host "[E2E] Tearing down..." -ForegroundColor Cyan
docker compose -f docker-compose.test.yml down -v

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "✅ E2E Tests Passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ E2E Tests Failed!" -ForegroundColor Red
    exit $ExitCode
}
