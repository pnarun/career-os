# Career OS — Beta readiness checklist

Operational readiness for controlled external beta and Chrome Web Store preparation.

## Beta launch checklist

- [ ] Production API deployed (Render) with `ENVIRONMENT=production`
- [ ] Frontend deployed (Vercel) with `FRONTEND_URL` set on API
- [ ] MongoDB Atlas and Upstash Redis configured
- [ ] `/health?detail=1` returns `ok` or acceptable `degraded`
- [ ] `/system/beta-ops` reviewed for active/stuck scans
- [ ] Career Lens extension v0.3.0+ packaged (no dev artifacts)
- [ ] Privacy policy live at `/privacy-policy` (landing + sidebar links)
- [ ] Beta welcome modal and Settings → Beta support tested
- [ ] Rate limits verified (scan trigger, pairing code, WebSocket caps)
- [ ] Email digest: one summary per scheduled scan (no duplicate blasts)
- [ ] Email logo renders in Gmail (inline `cid:` attachment from API static brand assets)

## Deployment checklist

### API (Render)

- Set required env: `MONGO_URI`, `JWT_SECRET_KEY`, `REDIS_URL` (or disable local Redis on cloud)
- Optional: `CRON_SECRET`, `RESEND_API_KEY`, `FRONTEND_URL`, `API_PUBLIC_URL`, `BRAND_LOGO_*_URL`, `EXTENSION_MIN_VERSION`
- Confirm startup logs show `startup_verification` with mongo/redis status
- Uptime monitor: `HEAD /health` (minimal) or `GET /health?detail=1` (full)

### Frontend (Vercel)

- SPA rewrite to `index.html` (default)
- Verify `/privacy-policy` loads without auth
- Update `extension/config.js` → `CAREER_OS_PRIVACY_URL` to match production domain

### Extension (unpacked beta)

- Bump `manifest.json` version to match `EXTENSION_MIN_VERSION` on API
- Zip `extension/` folder (exclude `PRIVACY.md` dev notes if desired; policy URL is web)
- Distribute to beta testers with pairing instructions

## Onboarding checklist

1. User signs up on Career OS
2. Uploads resume (onboarding gate)
3. Sees **Beta welcome** modal (extension → pair → first scan)
4. Installs Career Lens, logs into LinkedIn
5. Generates pairing code in **Scans & Automation**
6. Connects in extension popup
7. Configures job preferences in **Settings**
8. Runs first scan from Operations hub

## Operational checklist

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Minimal keep-alive (Redis + scheduler) |
| `GET /health?detail=1` | Mongo, WebSocket, scans, providers, cache ratio |
| `GET /system/status` | Component health JSON |
| `GET /system/metrics` | Observability counters |
| `GET /system/beta-ops/json` | Beta ops snapshot |
| `GET /system/beta-ops` | HTML ops dashboard |
| `GET /uptime` | Developer uptime hub |

Watch during beta:

- Stuck scans (`scan_subsystem.stuck_estimate` in beta-ops)
- Provider failure rate (`providers.failure_rate`)
- WebSocket connection count
- `rate_limit_blocked` metric spikes

## Recovery flows

### LinkedIn session expired

1. User sees reconnect guidance in Scans & Automation
2. Open Career Lens → confirm LinkedIn login → **Resync** or new pairing code
3. Disconnect + reconnect if sync token invalid

### Scan stuck

- Scans auto-fail after `SCAN_STALE_SECONDS` (default 2h)
- User starts a new scan; avoid parallel manual scans

### Backend unreachable

- Extension shows health banner; user checks API status / network
- Frontend **Backend wake** and WebSocket reconnect toast

### Extension outdated

- API returns HTTP 426; user installs latest beta build matching `EXTENSION_MIN_VERSION`

## Chrome Web Store preparation

- [ ] Privacy policy URL: `https://<your-domain>/privacy-policy`
- [ ] Single purpose description aligned with manifest
- [ ] Permissions justification (cookies, LinkedIn hosts) matches policy section
- [ ] Screenshots and listing copy (beta)
- [ ] `host_permissions` limited to LinkedIn + Career OS API
- [ ] Support email: support@career-lens.in
- [ ] Review `extension/PRIVACY.md` for internal notes; public policy is the web page

## Rate limits (default)

| Path | Limit |
|------|-------|
| `/run-scan-now`, `/scans/run` | 6 / minute / IP |
| `/automation/linkedin/connect-with-code` | 8 / 5 min / IP |
| `/automation/linkedin/pairing-code` | 6 / 5 min / IP |
| `/automation/linkedin/resync` | 20 / minute / IP |
| WebSocket | 5 per user, 200 total |

## Support

- In-app: **Settings → Beta support** (support ID + troubleshooting)
- Extension: **Copy diagnostics** (no secrets)
- Email: [support@career-lens.in](mailto:support@career-lens.in)
