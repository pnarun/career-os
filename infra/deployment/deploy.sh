#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV="${1:-staging}"

cd "$ROOT"
docker compose \
  -f docker-compose.yml \
  -f "infra/docker/docker-compose.${ENV}.yml" \
  build --pull

docker compose \
  -f docker-compose.yml \
  -f "infra/docker/docker-compose.${ENV}.yml" \
  up -d

echo "Deployed Career OS ($ENV)"
curl -sf "http://localhost/health" || curl -sf "http://localhost:8001/health" || true
