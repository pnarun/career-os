#!/usr/bin/env bash
# Poll health endpoints for monitoring / uptime checks
set -euo pipefail

API_URL="${API_URL:-http://localhost:8001}"

echo "Checking $API_URL/health"
curl -sf "$API_URL/health" | python -m json.tool

echo "Checking $API_URL/system/status"
curl -sf "$API_URL/system/status" | python -m json.tool
