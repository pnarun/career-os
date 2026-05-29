# Current phase status

Transparent snapshot — **May 2026**.

## Architectural maturity

| Area | Maturity | Notes |
|------|----------|-------|
| Modular monolith codebase | **High** | Single repo, clear packages |
| Distributed runtime | **Production** | API + scan worker on Render |
| Mongo scan queue | **Production** | Replaces inline API scans |
| Mongo scan state sync | **Production** | Polling reliable |
| Mongo realtime bus | **Production** | WS enhancement + poll fallback |
| Automation worker isolation | **Early** | Process exists; limited dequeue |
| Celery/Redis scale path | **Prepared** | Disabled in prod |
| Multi-region / HA | **Not started** | |

## Completed phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | Feature flags, diagnostics, scheduler safety | **Done** |
| 1A | Scan execution layer, task model | **Done** |
| 1B | Real worker deploy, scheduler on worker | **Done** |
| — | Health HTTP on workers (Render free) | **Done** |
| — | Mongo `scan_states` shared progress | **Done** |
| 5 | TTL indexes, storage reports | **Done** |
| 6 | Mongo realtime bridge | **Done** |

## Remaining / planned phases

| Phase | Goal | Status |
|-------|------|--------|
| 2 | Redis/Celery queue (optional scale) | **Planned** |
| 3 | Automation worker job dequeue | **Planned** |
| — | Job archival (>90 days) | **Planned** |
| — | WS scale-out (sticky/Redis) | **Planned** |
| — | Indeed proxy / residential IP | **Research** |

## Production readiness

| Capability | Ready? |
|------------|--------|
| User auth + dashboard | **Yes** |
| Background scans (distributed) | **Yes** |
| Scheduled scans | **Yes** (scan worker) |
| Realtime progress (WS) | **Yes** with poll fallback |
| Email digests | **Yes** |
| LinkedIn via extension + Playwright | **Yes** with session setup |
| Indeed reliability | **Partial** (403 common) |
| Auto-apply all boards | **Partial** |
| SOC2 / enterprise SSO | **No** |

## Known limitations (honest)

1. **Render cold starts** on free/starter tiers.
2. **~8s** max queue pickup latency (worker poll).
3. **~1.5s** realtime bridge latency.
4. **Single concurrent scan** per worker default.
5. **WebSocket** does not survive all mobile network changes — polling required.
6. **Indeed** and some boards block datacenter IPs.
7. **512MB Atlas** requires TTL discipline.
8. **Automation worker** not yet full Playwright isolation.
9. **Celery** documented but not production path.

## What investors / evaluators should know

- Architecture is **intentional**, not accidental complexity.
- Free-tier operation is a **first-class design constraint**, not a hack.
- Scale path exists (Redis queue, more workers) without rewrite.
- Product is **beta-ready** for motivated job seekers, not yet enterprise multi-tenant at scale.

## Documentation

This docs overhaul aligns markdown with implemented behavior. When code changes, update:

- [../architecture/overview.md](../architecture/overview.md)
- This file
- [../roadmap/future-roadmap.md](../roadmap/future-roadmap.md)
