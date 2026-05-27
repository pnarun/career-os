# Vision and goals

## Vision

Career OS becomes the **operating system for a modern job search** under Career Lens: one place to discover opportunities, understand fit, act on them, and improve candidacy over time—with trustworthy automation that respects platform limits and user control.

## Strategic goals

### Short term (MVP / production)

1. **Reliable scheduled scans** — APScheduler + startup catch-up on Render sleep
2. **Stable multi-provider feed** — HTTP sources + optional LinkedIn via saved session
3. **Production deploy** — Vercel + Render + Atlas with documented env and health checks
4. **Auth and preferences** — Per-user scan schedule, thresholds, target roles/skills
5. **Email digests** — Resend delivery with dedupe via `last_email_sent_at`

### Medium term

1. Persistent LinkedIn session storage on Render disk or secure blob store
2. Redis-backed rate limiting and optional Celery for heavy scans
3. Same-origin API proxy on Vercel to reduce ad-blocker false positives
4. Google OAuth completion (stub exists in backend)
5. Expanded auto-apply coverage with human-in-the-loop confirmations

### Long term

1. Team/workspace collaboration on shared pipelines
2. Employer-facing analytics (Career Lens B2B angle)
3. Mobile-optimized PWA as primary mobile experience
4. Multi-region deployment and read replicas

## Non-goals (current scope)

- Replacing LinkedIn/Indeed Terms of Service compliance review (users responsible for session use)
- Fully unattended mass auto-apply without user session preparation
- On-premise single-tenant enterprise (cloud-first today)

## Success metrics

| Metric | Indicator |
|--------|-----------|
| Scan reliability | Scheduled jobs run after Render wake; catch-up completes |
| Match quality | User feedback on high-match emails; threshold settings used |
| Uptime | `/health` Up on UptimeRobot; API cold start &lt; 90s |
| Engagement | Return visits, applications tracked, resume AI usage |
| Ops | Low ERROR rate in `/logs`; no scheduler NameError on deploy |

## Principles

1. **User-owned data** — Preferences, resumes, applications scoped per user/workspace
2. **Fail gracefully** — Provider circuit breakers; partial scan results still stored
3. **Observable automation** — Realtime timeline + structured logs
4. **Security by default** — JWT, refresh rotation, secrets only on backend
5. **Document everything** — This portal for onboarding and maintenance
