# Platform experience (customer view)

What job seekers experience when using Career OS — without implementation detail.

## What Career OS is

Career OS is an **AI-powered job search copilot** by ELVA Tech, part of the Career Lens ecosystem. It finds roles across multiple boards, scores them against your resume, and helps you act on the best matches from one dashboard.

## Core workflow

```mermaid
flowchart LR
  A[Upload resume] --> B[Set preferences]
  B --> C[Run scan]
  C --> D[Review ranked jobs]
  D --> E[Save / apply / track]
```

## What users see during a scan

1. Click **Scan** — immediate acknowledgment (scan started).
2. **Progress bar** moves through providers (LinkedIn, Indeed, Naukri, etc.).
3. **Jobs feed** fills with ranked opportunities.
4. Optional **email digest** with top matches.

## Realtime vs refresh

- Progress updates **live** when your browser maintains a connection.
- If the tab sleeps or connection drops, the app **keeps checking** until complete — you still get results.

**Transparent limitation:** Live updates may lag a few seconds behind backend processing.

## AI value

| Feature | Benefit |
|---------|---------|
| Match score | See fit at a glance |
| Resume AI | Improve ATS compatibility |
| Career Copilot | Ask questions about your search |
| Interview prep | Practice for specific roles |

## Trust & privacy

- Privacy policy available in-app
- LinkedIn connection via official extension pairing (not storing password in Career OS)
- Your data stays in your account workspace

## Beta status

Career OS is **production-capable** for motivated users with known provider limitations (some job boards may return fewer results due to anti-bot policies).

See [saas-vision.md](./saas-vision.md) and [competitive-advantages.md](./competitive-advantages.md).
