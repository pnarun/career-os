# Engineering decisions

Recorded architectural choices for Career OS. Use this when proposing changes.

## ADR-001: FastAPI + Motor async

**Decision:** Async FastAPI with Motor for MongoDB.  
**Rationale:** Concurrent I/O for multi-provider job fetches and WebSockets.  
**Trade-off:** Playwright must not block event loop → subprocess workers.

## ADR-002: Playwright in subprocess

**Decision:** `worker_cli` subprocess per automation command.  
**Rationale:** Stability, timeout isolation, no chromium in uvicorn process.  
**Trade-off:** Higher latency vs in-process; JSON IPC overhead acceptable.

## ADR-003: APScheduler in API process

**Decision:** Run scheduler inside API container, not separate worker.  
**Rationale:** Simpler Render deploy for MVP; catch-up on wake handles sleep.  
**Trade-off:** Scale-out requires leader election or external cron; Celery optional later.

## ADR-004: No React Router for app pages

**Decision:** `useState` + `sessionStorage` for navigation; URL stays `/`.  
**Rationale:** Avoid `/settings` URL leaks; simpler Vercel SPA; persist page on refresh.  
**Trade-off:** No deep-linkable pages; share links always land on home.

## ADR-005: JWT + refresh rotation

**Decision:** Stateless access JWT; refresh tokens stored hashed server-side.  
**Rationale:** Horizontal scaling without session store for access tokens.  
**Trade-off:** Cannot revoke access token before expiry without blocklist (not implemented).

## ADR-006: Lightweight /health vs /system/status

**Decision:** `/health` no DB; `/system/status` full checks.  
**Rationale:** UptimeRobot and cold-start probes must not hammer Mongo.  
**Trade-off:** Monitor may show Up while DB is down — use status page for deep checks.

## ADR-007: Provider circuit breakers

**Decision:** Per-provider circuit breaker in aggregator.  
**Rationale:** One slow board must not block entire scan.  
**Trade-off:** Partial feeds common; UI must show provider diagnostics.

## ADR-008: Realtime via WebSocket + optional Redis

**Decision:** In-process fan-out default; Redis pub/sub for multi-worker future.  
**Rationale:** Single Render instance MVP.  
**Trade-off:** Multiple replicas need Redis bridge wired for all emitters.

## ADR-009: Gemini for AI features

**Decision:** Google Gemini for resume, copilot, interview, scoring.  
**Rationale:** Single provider simplifies keys and SDK.  
**Trade-off:** Vendor lock-in; fallback behavior if key missing.

## ADR-010: Vercel + Render split

**Decision:** Static frontend on Vercel; Docker API on Render.  
**Rationale:** Best fit per workload; Playwright in Docker.  
**Trade-off:** CORS and cold start complexity; consider API proxy later.

## ADR-011: Structured JSON logging + in-memory viewer

**Decision:** JSON logs to stdout + ring buffer for `/logs` HTML UI.  
**Rationale:** Fast debugging on Render without external APM cost.  
**Trade-off:** Logs lost on restart; not centralized — add Datadog later if needed.

## ADR-012: India-focused eligibility filters

**Decision:** `actionable_in_india`, `remote_priority` for email alerts.  
**Rationale:** Reduce irrelevant foreign onsite roles in digests.  
**Trade-off:** May hide valid relocation roles; user can use feed filters.

## Revisit later

- [ ] Vercel rewrites for same-origin API (ad-blocker mitigation)
- [ ] Google OAuth completion
- [ ] Persistent LinkedIn sessions on Render disk
- [ ] Celery for long scans when Redis enabled
- [ ] Authenticate `/logs` viewer
