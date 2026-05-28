# Onboarding experience — trust & clarity

Career OS should feel like a calm, trustworthy SaaS product. This document describes the in-product onboarding patterns (Phase 2 polish).

## Principles

- **Transparent** — Say what we access, what we don't, and why desktop setup exists once.
- **Non-technical** — Avoid Playwright, selectors, cookies jargon in primary UI (details live in Settings → Privacy & automation).
- **Never stuck** — Loading, retry, reconnect, and live-update states always explain what's happening.

## LinkedIn automation (Career Lens)

### User-facing flow (desktop)

1. Install **Career Lens** Chrome extension (one-time, desktop Chrome).
2. Log into LinkedIn in the same Chrome profile.
3. In Career OS → **Scans & Automation** → **Automation**, tap **Generate pairing code**.
4. In Career Lens, enter the 6-digit code and tap **Connect**.
5. Confirm **Automation active** on the status panel.

### Mobile

- Explain that **desktop setup is required once**.
- After connection, scans and jobs sync in the cloud; the mobile web app works normally.

### Trust copy (canonical)

- "Career Lens only uses your LinkedIn session to fetch jobs you already have access to."
- "We never collect passwords or browsing history."
- "Setup is required only once on desktop."

### Status center (Automation tab)

| Indicator | Meaning |
|-----------|---------|
| Connected | Server has a saved LinkedIn session |
| Last synced | Last time session cookies were refreshed |
| Session healthy | Session is valid for imports |
| Reconnect needed | Stale or invalid — generate a new pairing code |
| Career Lens | Extension step — inferred from connection / pairing state |

### Screenshots (placeholders)

Add marketing screenshots under `docs/assets/ui/onboarding/`:

| File | Description |
|------|-------------|
| `linkedin-step-1-extension.png` | Chrome extensions page with Career Lens |
| `linkedin-step-2-pairing-code.png` | Career OS pairing code card |
| `linkedin-step-3-extension-connect.png` | Career Lens pairing screen |
| `linkedin-step-4-connected.png` | Green "Automation active" state |

## Other onboarding surfaces

| Surface | Pattern |
|---------|---------|
| Resume | `ResumeOnboardingModal` — resume powers matching |
| Platform tour | `PlatformTour` — first-login walkthrough |
| Slow loading | `SlowLoadingPageCenter` + rotating messages |
| Empty states | `EmptyState` component — jobs, scans, analytics |

## Error messaging

Technical errors are mapped in `frontend/src/lib/userFacingErrors.js`:

- `401` / session → reconnect guidance
- Timeouts → "keep trying in the background"
- Selector issues → "retry in a few minutes"

## Extension FAQ (short)

**Why an extension?**  
LinkedIn doesn't offer a public API for personalized job search. Career Lens securely bridges your existing login to Career OS — once.

**Is my password shared?**  
No. Only session cookies after you approve pairing.

**Can I disconnect?**  
Yes — in Career Lens, Automation tab, or Settings → Privacy & automation → Delete LinkedIn session.

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Pairing code expired | Generate a new code (5-minute window) |
| "Reconnect needed" | Log into LinkedIn in Chrome, open Career Lens → Resync |
| No jobs after connect | Run **Fetch LinkedIn Jobs** or a full scan from Scans |
| Imports fail after 90+ days | Reconnect session from Automation tab |

## Related docs

- `docs/automation/linkedin-session-management.md` — technical session lifecycle
- `docs/extension/local-development.md` — developer extension load
- Public privacy policy: `/privacy-policy` (`PrivacyPolicyPage.jsx`); `extension/PRIVACY.md` is internal notes for store review
