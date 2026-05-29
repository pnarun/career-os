# Privacy and security (product)

## Data we store

- Account (email, hashed password or OAuth linkage)
- Resume and profile preferences
- Scanned jobs and application tracking
- LinkedIn session artifacts (encrypted storage in Mongo — browser state for automation)
- Notifications and scan history (TTL-limited)

## What we do not sell

User job data is not sold to third parties as a product feature. SaaS terms should be finalized before public launch.

## Session security

- JWT access + refresh tokens
- HTTPS only in production (Vercel + Render)
- Extension communicates with API over HTTPS with user auth

## Automation transparency

LinkedIn automation uses **your** logged-in session via the extension — not shared pools of credentials.

## Data retention

Operational collections expire via Mongo TTL (7–30 days for scans/events/sessions metadata). Long-term job retention archival is **Planned** (90d+).

Technical: [../architecture/security-model.md](../architecture/security-model.md).

## Reporting issues

Security issues: contact ELVA Tech via production support channel (define before public beta).
