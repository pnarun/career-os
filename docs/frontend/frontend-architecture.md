# Frontend architecture

## Stack

| Technology | Version / notes |
|------------|-----------------|
| React | 19 |
| Vite | 6 |
| TypeScript | Partial (pages mix `.tsx` / `.jsx`) |
| Tailwind CSS | v4 via `@tailwindcss/vite` |
| TanStack Query | Server state for dashboard, jobs, etc. |
| Recharts | Analytics charts |
| Job list pagination | `VirtualizedJobGrid.jsx` + `JobListPagination.jsx` (6 per page, CSS grid) |

**No React Router** for in-app pages — see navigation below.

## Bootstrap (`src/main.tsx`)

Provider tree:

```text
AppErrorBoundary
  QueryClientProvider
    BackendWakeProvider      # /health polling, Render cold start
      AuthProvider           # session, login/logout
        RealtimeProvider     # WebSocket when authenticated
          App
```

Dark theme: `document.documentElement.classList.add("dark")` on load.

PWA: service worker registered in production only (`/sw.js`).

## Auth gate (`src/App.tsx`)

| State | UI |
|-------|-----|
| `loading && !authenticated` | Full-screen slow loading |
| `isAuthenticated` | `ResumeOnboardingProvider` → `AppShell` |
| else | `LandingPage` + `LandingAuthFlow` modal |

## Navigation

**State:** `AppPage` union type in `Sidebar.tsx`  
**Persistence:** `sessionStorage` via `src/lib/appNavigation.ts`  
**URL:** Always `/` (no `/settings` paths)

### Top-level pages

| `AppPage` | Component | Description |
|-----------|-----------|-------------|
| `dashboard` | `DashboardPage.tsx` | Overview stats |
| `resume-hub` | `ResumeHub.jsx` | Upload + Resume AI tabs |
| `jobs-hub` | `JobsHub.jsx` | Feed + Job Match |
| `career-hub` | `CareerHub.jsx` | Applications + Interview |
| `insights-hub` | `InsightsHub.jsx` | Analytics + Copilot |
| `operations-hub` | `OperationsHub.jsx` | Scans, Automation, Notifications |
| `settings` | `Settings.jsx` | Preferences |
| `profile` | `Profile.jsx` | Account |

Hubs use `TabbedHub.tsx` for sub-tabs.

## API client (`src/lib/apiClient.js`)

```javascript
// Production must set at build time:
VITE_API_BASE_URL=https://your-api.onrender.com
VITE_WS_BASE_URL=wss://your-api.onrender.com  // optional
```

- Tokens: `career_os_access_token`, `career_os_refresh_token` in `localStorage`
- `apiFetch(path, options)` — attaches Bearer, refreshes on 401
- `refreshAccessToken()` — exported for WebSocket reconnect

## Backend wake (`BackendWakeContext.jsx`)

Solves Render cold start:

1. On mount: `waitForBackendReady()` — polls `GET /health` up to ~60s
2. Exposes `ready`, `waking`, `failed`, `retryWake`
3. Keepalive every **5 minutes** when online (matches UptimeRobot)
4. `WakeAwareButton` disables CTAs until `ready`

**Note:** `net::ERR_BLOCKED_BY_CLIENT` in console is usually an **ad blocker**, not CORS. Test in Incognito or whitelist domains.

## Realtime (`realtimeClient.js` + `RealtimeContext.jsx`)

- Connects when `isAuthenticated`
- URL: `{ws}/ws/realtime?token=...`
- Reconnect with exponential backoff
- On close `4401`/`4403`: refresh token then reconnect; else stop
- Feeds: scan timeline, toasts, `feedVersion` bump for Jobs grid

## Service modules (`src/services/`)

One file per backend domain, e.g.:

- `authService.js`, `jobService.js`, `preferencesService.js`
- `scansService.js`, `automationService.js`, `resumeAiService.js`
- `careerAnalyticsService.js`, `copilotService.js`, `interviewAiService.js`

All use `apiFetch` from `apiClient.js`.

## UI patterns

| Pattern | Component |
|---------|-----------|
| App shell | `DashboardLayout.tsx` — sidebar, navbar, footer |
| Modals | `AppModal.jsx` — center/top, glass backdrops |
| Confirm | `ConfirmDialog.jsx` |
| Job modals | `JobDetailsModal`, `JobDescriptionModal`, etc. |
| Paginated job grid | `VirtualizedJobGrid.jsx`, `JobListPagination.jsx` |
| Public legal page | `PrivacyPolicyPage.jsx` — `/privacy-policy` (bootstrapped in `main.tsx`, no auth) |
| Beta UX | `BetaWelcomeModal.jsx`, `BetaSupportSection.jsx` (Settings) |
| Onboarding | `ResumeOnboardingModal`, `PlatformTour` |
| Footer | `SiteFooter.jsx` — Career Lens / ELVA Tech links |

## Build & deploy

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build → dist/
```

**Vercel:** root directory `frontend`, `vercel.json` SPA rewrite to `index.html`.

Manual chunks in `vite.config.ts`: `vendor` (react), `charts` (recharts).

## Environment

See [Environment variables](../deployment/environment-variables.md).

Debug UI (`DebugSummaryPanel`, historical debug on Jobs) only when `import.meta.env.DEV`.

## Related

- [UI walkthrough](../ui/ui-walkthrough.md)
- [Deployment](../deployment/render-vercel-deployment.md)
