# API reference

**Base URL:** `https://your-api.onrender.com` (no `/api` prefix)

**Interactive docs:** `/docs` and `/redoc` when enabled (non-prod or `is_cloud_deploy`)

**Auth:** `Authorization: Bearer <access_token>` unless noted.

## System

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| HEAD | `/` | No | Render probe → 200 |
| HEAD | `/health` | No | UptimeRobot keep-alive |
| GET | `/health` | No | JSON health + scheduler |
| GET | `/health?detail=1` | No | Extended health (Mongo, WebSocket, scans, providers, cache) |
| GET | `/system/status` | No | Full dependency status |
| GET | `/system/metrics` | No | Metrics snapshot |
| GET | `/system/beta-ops` | No | HTML beta ops dashboard |
| GET | `/system/beta-ops/json` | No | Beta ops snapshot JSON |
| GET | `/brand/{filename}` | No | Static brand PNGs (email/HTML fallbacks) |
| GET | `/logs` | No | HTML log viewer |
| GET | `/logs/api` | No | JSON logs |
| POST | `/internal/cron/scheduled-scans` | `X-Cron-Secret` | Trigger catch-up |

## Auth (`/auth`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/check-email` | `{ email }` → exists, full_name |
| POST | `/auth/register` | Create account + tokens |
| POST | `/auth/login` | Login + tokens |
| POST | `/auth/refresh` | `{ refresh_token }` → new tokens |
| POST | `/auth/logout` | Revoke refresh |
| POST | `/auth/password-reset/request` | Send OTP email |
| POST | `/auth/password-reset/confirm` | Reset with OTP |
| GET | `/auth/me` | Current user |
| PATCH | `/auth/me` | Update profile |
| PATCH | `/auth/password` | Change password |
| GET | `/auth/workspaces` | List workspaces |

### Auth response example

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "full_name": "Arun",
    "timezone": "Asia/Kolkata"
  }
}
```

## Realtime

| Method | Path | Description |
|--------|------|-------------|
| WS | `/ws/realtime?token=<access_jwt>` | User-scoped events |

**Server → client events:** `connected`, `scan_started`, `scan_completed`, `scan_failed`, `jobs_fetched`, `ai_scoring_complete`, `provider_status`, `provider_batch`, `notification`, `pong`

## Jobs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/fetch-jobs` | Trigger provider fetch |
| POST | `/fetch-linkedin` | LinkedIn-specific fetch |
| GET | `/jobs` | List jobs |
| GET | `/jobs/feed` | Unified feed (filters) |
| GET | `/jobs/history` | Historical batches |

## Scan

| Method | Path | Description |
|--------|------|-------------|
| POST | `/run-scan-now` | Manual full scan |
| POST | `/send-email-now` | Send digest now |
| GET | `/email-preview` | Preview email HTML |

## Preferences

| Method | Path | Description |
|--------|------|-------------|
| POST | `/preferences` | Create |
| GET | `/preferences` | Get current user |
| PUT | `/preferences/{id}` | Update |

## Applications

| Method | Path | Description |
|--------|------|-------------|
| POST | `/applications/save` | Save job |
| POST | `/applications/apply` | Mark applied |
| GET | `/applications` | List |
| PATCH | `/applications/{id}` | Update status |
| GET | `/applications/analytics` | Funnel stats |

## Resume & match

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload-resume` | Upload file |
| GET | `/resumes` | List resumes |
| POST | `/match-job` | Score one job |

## Resume AI (`/resume-ai/*`)

Overview, ATS score, feedback, keywords, skill gaps, variants, align, tailor, export — see OpenAPI `/docs`.

## Interview prep (`/interview-prep/*`)

Jobs list, overview, readiness, questions, plan, mock interview, practice, progress.

## Career analytics (`/career-analytics/*`)

Dashboard, salary, market trends, skill demand, funnel, providers, growth, transitions, heatmap, weekly insights.

## Copilot

| Method | Path | Description |
|--------|------|-------------|
| GET | `/copilot/overview` | Context summary |
| POST | `/copilot/chat` | Chat message |
| POST | `/copilot/quick-action` | Preset actions |

## Automation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/automation/browser-health` | Playwright worker |
| GET | `/automation/session-status` | LinkedIn session |
| POST | `/automation/prepare-session` | Start session prep |
| DELETE | `/automation/session` | Clear session |

## Notifications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications` | List |
| PATCH | `/notifications/{id}/read` | Mark read |
| POST | `/notifications/read-all` | Mark all read |

## Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/summary` | Aggregated stats |

## Suggestions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/suggestions/roles` | Tag autocomplete |
| GET | `/suggestions/skills` | |
| GET | `/suggestions/companies` | |
| GET | `/suggestions/locations` | |

## Error format

FastAPI default:

```json
{
  "detail": "Human-readable message"
}
```

Or validation:

```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

## Rate limiting

When `RATE_LIMIT_ENABLED=true`, auth and heavy routes may return `429`. See `app/core/rate_limit.py`.

## Related

- [Backend architecture](../backend/backend-architecture.md)
- [Security](../security/security-model.md)
