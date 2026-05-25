#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV="${1:-development}"

echo "==> Bootstrapping Career OS ($ENV)"

cd "$ROOT/backend"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

if [[ ! -f .env ]]; then
  cp ".env.${ENV}" .env 2>/dev/null || cp .env.example .env
  echo "Created backend/.env from template"
fi

cd "$ROOT/frontend"
npm install

echo "==> Starting Redis (Docker)"
cd "$ROOT"
docker compose up -d redis

echo "==> Done. Run backend: cd backend && uvicorn app.main:app --port 8001 --reload"
echo "==> Run frontend: cd frontend && npm run dev"
