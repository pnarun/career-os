# Dashboard (product)

## Main areas

| Area | Purpose |
|------|---------|
| **Jobs feed** | Scanned roles, match scores, filters, target companies |
| **Scans** | Start/monitor background scans, progress panel |
| **Automation** | LinkedIn connect, extension pairing |
| **Resume** | ATS, keywords, variants |
| **Analytics** | Application trends, salary (INR), role breakdown |
| **Copilot** | AI career Q&A |
| **Settings** | Roles, skills (tags), scan schedule, notifications |

## Realtime behavior

- Progress updates via WebSocket when connected
- **Polling always runs** as fallback (Render WS limitations)

Users may see ~1–2s delay vs worker — normal on free tier.

## Notifications

- In-app bell (scan complete, system)
- Email for scheduled scans (Resend) when configured

See [../features/email-notifications.md](../features/email-notifications.md).
