# UI walkthrough

Career OS uses a **hub-based** navigation model with a persistent sidebar (desktop) and bottom nav (mobile).

## Information architecture

```mermaid
flowchart TB
  L[Landing /] --> AUTH[Auth modals]
  AUTH --> D[Dashboard]
  D --> RH[Resume hub]
  D --> JH[Jobs hub]
  D --> CH[Career hub]
  D --> IH[Intelligence hub]
  D --> OH[Operations hub]
  D --> ST[Settings]
  D --> PR[Profile]
  RH --> RU[Upload]
  RH --> RA[Resume AI]
  JH --> JF[Jobs feed]
  JH --> JM[Job match]
  CH --> AP[Applications]
  CH --> IP[Interview prep]
  IH --> CA[Analytics]
  IH --> CP[Copilot]
  OH --> SC[Scans]
  OH --> AU[Automation]
  OH --> NT[Notifications]
```

## Landing (unauthenticated)

**File:** `LandingPage.jsx`

- Hero: “Find, match, and land your next role”
- CTAs: Sign in, Get started free
- Footer: Career Lens / ELVA Tech links
- Opens `LandingAuthFlow` modal (email → login/register/forgot)

![Landing](../assets/screenshots/landing-hero.png)

**Wake state:** Blue banner when API cold-starting; `WakeAwareButton` disables Continue until `/health` ok.

## Dashboard

**File:** `DashboardPage.tsx`

- Summary cards (applications, scans, insights)
- Quick links to hubs
- React Query loaded metrics

![Dashboard](../assets/screenshots/dashboard-overview.png)

## Resume hub

| Tab | Page | Actions |
|-----|------|---------|
| Upload | `ResumeUpload.jsx` | PDF/DOCX upload, list resumes |
| AI | `ResumeAI.jsx` | ATS, keywords, tailor |

## Jobs hub

| Tab | Page | Actions |
|-----|------|---------|
| Feed | `Jobs.jsx` | Filter, sort, save, apply modals, paginated grid (6/page) |
| Match | `JobMatch.jsx` | Paste JD URL/text, score |

**Modals:** `JobDetailsModal`, `JobDescriptionModal`, `ApplyAssistantModal`

![Jobs feed](../assets/screenshots/jobs-feed.png)

## Career hub

| Tab | Page |
|-----|------|
| Applications | `Applications.jsx` — pipeline board |
| Interview | `InterviewPrep.jsx` |

## Intelligence hub

| Tab | Page |
|-----|------|
| Analytics | `CareerAnalytics.jsx` |
| Copilot | `CareerCopilot.jsx` — chat UI |

## Operations hub

| Tab | Page |
|-----|------|
| Scans | `Scans.jsx` — schedule, run now, timeline |
| Automation | `Automation.jsx` — LinkedIn session |
| Notifications | `Notifications.jsx` |

![Scans timeline](../assets/screenshots/scans-timeline.png)

## Settings

**File:** `Settings.jsx`

- Scan schedule, timezone, frequency
- Target roles/skills/companies/locations (`TagCombobox`)
- Provider toggles, match threshold
- Notification preferences

![Settings](../assets/screenshots/settings-preferences.png)

## Global UX elements

| Element | Location |
|---------|----------|
| Sidebar | `Sidebar.tsx` — “Career OS” → dashboard |
| Top navbar | `TopNavbar.tsx` — notifications bell |
| User menu | `UserMenu.jsx` — profile, logout |
| Platform tour | `PlatformTour` — first login |
| Resume onboarding | `ResumeOnboardingModal` — new users |
| Realtime toasts | `RealtimeToastHost` |
| PWA install | `PwaInstallPrompt` |

## Mobile

- Sidebar collapses to overlay
- `MobileBottomNav.tsx` — 5 primary hubs
- Modals use top-center placement below header

![Mobile nav](../assets/screenshots/mobile-bottom-nav.png)

## Design system

- Dark theme default (neon/glass accents)
- Tailwind utility classes
- shadcn-style `Button`, `Card` in `components/ui/`
- Orange/yellow chart tooltips in analytics

## Related

- [Frontend architecture](../frontend/frontend-architecture.md)
- [Screenshots checklist](../assets/README.md)
