# Documentation assets

Place visual assets here so product, engineering, and demo docs stay consistent.

## Directory structure

```text
docs/assets/
├── screenshots/     # UI captures for walkthroughs and README
├── diagrams/        # Exported PNG/SVG from Mermaid or design tools
├── ui/              # Component-level UI shots
└── workflows/       # Step-by-step flow screenshots
```

## Required screenshots (checklist)

Capture these from **production** or **staging** and save with the exact filenames below.

### Landing & auth

| File | What to capture |
|------|-----------------|
| `screenshots/landing-hero.png` | Landing page hero + CTAs |
| `screenshots/landing-auth-email.png` | Auth modal — email step |
| `screenshots/landing-auth-login.png` | Auth modal — sign in |
| `screenshots/landing-wake-banner.png` | “Waking up servers…” state (optional) |

### Dashboard & navigation

| File | What to capture |
|------|-----------------|
| `screenshots/dashboard-overview.png` | Main dashboard with stats |
| `screenshots/sidebar-navigation.png` | Sidebar + hub labels |
| `screenshots/mobile-bottom-nav.png` | Mobile layout |

### Jobs & applications

| File | What to capture |
|------|-----------------|
| `screenshots/jobs-feed.png` | Jobs feed with filters |
| `screenshots/job-details-modal.png` | Job details modal |
| `screenshots/job-match.png` | Job Match page |
| `screenshots/applications-pipeline.png` | Applications CRM view |

### Resume & AI

| File | What to capture |
|------|-----------------|
| `screenshots/resume-upload.png` | Resume upload hub |
| `screenshots/resume-ai-ats.png` | Resume AI ATS / scores |

### Operations

| File | What to capture |
|------|-----------------|
| `screenshots/scans-timeline.png` | Scans page + live timeline |
| `screenshots/automation-sessions.png` | Automation / browser sessions |
| `screenshots/notifications-center.png` | Notifications list |

### Settings & analytics

| File | What to capture |
|------|-----------------|
| `screenshots/settings-preferences.png` | Settings — roles, skills, schedule |
| `screenshots/career-analytics.png` | Analytics charts |
| `screenshots/career-copilot.png` | Copilot chat |

### Ops / deploy

| File | What to capture |
|------|-----------------|
| `screenshots/render-dashboard.png` | Render service live |
| `screenshots/vercel-env.png` | Vercel env vars (redact secrets) |
| `screenshots/uptimerobot-monitor.png` | UptimeRobot HEAD /health Up |
| `screenshots/api-logs-viewer.png` | `/logs` on API |

### Diagrams (optional exports)

| File | Source |
|------|--------|
| `diagrams/system-overview.png` | Export from `architecture/system-overview.md` Mermaid |
| `diagrams/scan-pipeline.png` | Export from `automation/job-aggregation-pipeline.md` |

## Markdown usage

```markdown
![Jobs feed](../assets/screenshots/jobs-feed.png)

*Figure: Unified job feed with provider filters and match scores.*
```

## Privacy

- Redact emails, API keys, and JWT tokens in screenshots.
- Use demo accounts (`*.demo`) where possible.
