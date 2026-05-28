# Production readiness checklist

Use before launch, major releases, or investor demos.

## Infrastructure

- [ ] MongoDB Atlas production cluster with backups
- [ ] Render web service **Live** on Starter or above (if budget allows)
- [ ] Vercel production + preview env vars set
- [ ] UptimeRobot monitor **Up** on `HEAD /health`
- [ ] `JWT_SECRET_KEY` strong and stable
- [ ] `REDIS_ENABLED=false` unless Redis provisioned
- [ ] `AUTH_DEV_EXPOSE_OTP=false`
- [ ] `AUTH_SEED_DEMO_USERS=false`

## Security

- [ ] No secrets in frontend bundle
- [ ] `FRONTEND_URL` matches production Vercel URL
- [ ] `CORS_ORIGIN_REGEX` for preview deploys
- [ ] Atlas IP allowlist configured
- [ ] `/logs` not publicly exposed (or IP restricted)
- [ ] HTTPS only (`https://` API URL on Vercel)

## Functional smoke test

- [ ] Register new user
- [ ] Login / logout / refresh token
- [ ] Upload resume
- [ ] Save preferences with `resume_id`
- [ ] Manual scan completes
- [ ] Jobs feed shows results
- [ ] Save application + update status
- [ ] WebSocket connects (no token spam in logs)
- [ ] Email digest sends (Resend dashboard)
- [ ] Resume AI returns scores (Gemini)
- [ ] Password reset email (if enabled)

## Performance

- [ ] Cold start &lt; 90s acceptable for demo
- [ ] Jobs feed paginated (6 cards/page) — no overlap or DOM freeze on large feeds
- [ ] Playwright Docker build succeeds on Render
- [ ] `WEB_CONCURRENCY=1` if memory constrained

## Observability

- [ ] Structured logs visible on Render
- [ ] `/system/status` shows Mongo ok
- [ ] Scheduler `running` in `/health`
- [ ] No repeating ERROR on idle (WS, catch-up)

## Documentation

- [ ] `docs/README.md` portal current
- [ ] Screenshots captured per `docs/assets/README.md`
- [ ] Deploy runbook shared with team
- [ ] Known issues in troubleshooting doc

## Legal / product

- [ ] Privacy policy live at `/privacy-policy` (landing footer + sidebar; extension `config.js` URL matches prod)
- [ ] Terms for automation / third-party boards
- [ ] Career Lens / ELVA Tech branding correct in footer

## Post-launch monitoring (first 48h)

| Check | Frequency |
|-------|-----------|
| UptimeRobot | Continuous |
| Render logs ERROR count | Daily |
| Resend bounce rate | Daily |
| Atlas metrics | Daily |
| User-reported scan misses | As needed |

## Rollback plan

1. Revert Render deploy to previous image
2. Revert Vercel deployment
3. Do **not** rotate `JWT_SECRET_KEY` without comms (forces re-login)

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering | | |
| Product | | |
| DevOps | | |
