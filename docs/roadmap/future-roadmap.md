# Future roadmap

Prioritized direction for Career OS under Career Lens. Not a commitment schedule.

## Q2 2026 — Stability & production hardening

| Item | Priority | Notes |
|------|----------|-------|
| Vercel API proxy (`/api` → Render) | High | Fix ad-blocker false positives |
| Authenticated `/logs` or IP restrict | High | Security |
| Persistent LinkedIn sessions | High | Render disk |
| Google OAuth | Medium | Stub exists |
| E2E test suite (Playwright + API) | Medium | CI gate |

## Q3 2026 — Growth features

| Item | Priority | Notes |
|------|----------|-------|
| Deep links / shareable job URLs | Medium | Optional react-router hybrid |
| Team workspaces | Medium | Shared pipelines |
| Mobile PWA polish | Medium | Offline shell |
| More job providers | Medium | Adapter pattern ready |
| Salary data enrichment | Low | External APIs |

## Q4 2026 — Scale & enterprise

| Item | Priority | Notes |
|------|----------|-------|
| Redis + Celery default on | Medium | Heavy scans off API thread |
| Multi-region API | Low | Latency |
| SSO / SAML | Low | B2B Career Lens |
| Audit log export | Low | Compliance |
| Public API for partners | Low | API keys per workspace |

## Technical debt

- Consolidate `_utc_now_iso` into `app/core/datetime_utils.py`
- TypeScript migration for remaining `.jsx` pages
- Rate limit without Redis fallback mode
- Complete Redis realtime fan-out for all emitters
- Remove demo users from production DB

## Career Lens platform integration

- Unified auth with Career Lens parent site
- Cross-product analytics
- Shared branding assets in `docs/assets/`

## How to propose features

1. Open issue with user story + acceptance criteria
2. Update relevant `docs/features/*.md`
3. Add screenshot placeholders to `docs/assets/README.md`
4. Link ADR in `engineering-decisions.md` if architectural
