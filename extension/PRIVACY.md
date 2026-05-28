# Career Lens — Privacy

Career Lens is the official Chrome extension for [Career OS](https://github.com/). It exists only to bridge your **LinkedIn login session** to your Career OS account for job discovery automation.

## What we access

- **LinkedIn cookies** on `linkedin.com` (including the `li_at` session cookie) when you choose to connect or resync.
- **Extension local state** (connection status, sync token, last sync time).

## What we do not access

- Your LinkedIn password (never read or transmitted).
- Your browsing history on other sites.
- Page content, messages, or feed data from LinkedIn.
- Career OS account passwords (authentication uses a one-time pairing code from the web app).

## How data is used

1. You generate a **6-digit pairing code** in Career OS (while logged in on the web).
2. You enter that code in the extension while logged into LinkedIn in Chrome.
3. The extension sends LinkedIn session cookies to **your** Career OS API over HTTPS.
4. Career OS stores an encrypted browser session for **your user only** and uses it for server-side job search automation.
5. A **sync token** is stored in extension local storage so the extension can refresh the session periodically without asking for a new pairing code.

## Storage

| Location | Data |
|----------|------|
| Chrome extension storage | Sync token, last sync time, connection flags |
| Career OS backend (MongoDB) | Playwright-compatible session + sync token tied to your account |

## Retention

- Disconnecting in the extension or Career OS removes the server session.
- You can delete your Career OS account per platform policy.

## Permissions

| Permission | Why |
|------------|-----|
| `cookies` | Read LinkedIn auth cookies for session sync |
| `storage` | Save settings and connection state locally |
| `tabs` | Open LinkedIn login when needed |
| `alarms` | Periodic silent session refresh (every ~5 hours) |

## Contact

For privacy questions, contact the Career OS project maintainers.
