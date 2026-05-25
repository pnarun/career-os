# Windows dev bootstrap
param(
    [string]$Environment = "development"
)

$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Write-Host "==> Bootstrapping Career OS ($Environment)"

Push-Location "$Root\backend"
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\playwright install chromium
if (-not (Test-Path .env)) {
    if (Test-Path ".env.$Environment") { Copy-Item ".env.$Environment" .env }
    else { Copy-Item .env.example .env }
}
Pop-Location

Push-Location "$Root\frontend"
npm install
Pop-Location

Push-Location $Root
docker compose up -d redis
Pop-Location

Write-Host "==> Done. Backend: cd backend; .\.venv\Scripts\uvicorn app.main:app --port 8001 --reload"
Write-Host "==> Frontend: cd frontend; npm run dev"
