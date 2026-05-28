# Tab prefetching strategy

Career OS grouped hubs (Scans & Automation, Intelligence) load the active tab first, then **stagger-prefetch** lightweight sibling tab data so tab switches feel instant.

## Why

- Users often visit multiple tabs in the same hub during one session.
- Waiting on each tab’s first fetch feels sluggish compared to SaaS products that prefetch likely-next views.

## What we prefetch

| Hub (sidebar) | Active tab | Background prefetch |
|---------------|------------|---------------------|
| Scans & Automation | Scans | Automation bootstrap, Notifications |
| Scans & Automation | Automation | Scan center, Notifications |
| Scans & Automation | Notifications | Scan center, Automation bootstrap |
| Intelligence | Analytics | Copilot overview + history (light) |
| Intelligence | Copilot | *(none — analytics dashboard is heavy)* |
| Jobs | Jobs Feed | *(none — match is on-demand)* |
| Jobs | Job Match | Default jobs feed |
| Career Track | Applications | Interview prep job list |
| Career Track | Interview Prep | Applications + analytics |
| Resume | Upload Resume | Resume AI overview, resume list |
| Resume | Resume AI | Resume list |

## What we do **not** prefetch

- Career analytics dashboard (`/career-analytics/dashboard`)
- Full scan history dumps
- Playwright / automation actions
- Job feed pages

## Implementation

- **React Query** `queryClient.prefetchQuery()` only — no duplicate manual fetches.
- **Stagger**: ~500ms delay after hub mount, then ~280ms between sibling prefetches (`requestIdleCallback` when available).
- **Cache**: Respects existing `staleTime` from `STALE_TIMES`; skips prefetch when data is still fresh (`PREFETCH_SKIPPED_CACHE_HIT` in dev).
- **In-flight dedupe**: Skips if the same query is already fetching.

### Key files

- `frontend/src/lib/hubTabPrefetch.ts` — prefetch registry and scheduling
- `frontend/src/hooks/useHubTabPrefetch.ts` — hub hook
- `frontend/src/lib/prefetchDiagnostics.ts` — dev console logs

### Query keys

- `queryKeys.scans.center()`
- `queryKeys.operations.automationBootstrap()`
- `queryKeys.operations.notifications(tab)`
- `queryKeys.insights.copilotOverview()`

## Memory

- Prefetch uses the same React Query `gcTime` as normal queries (10 minutes default).
- We only cache summary/list endpoints, not large job arrays beyond existing scan center payload.

## Dev instrumentation

In development, watch the console for:

- `PREFETCH_STARTED`
- `PREFETCH_SKIPPED_CACHE_HIT`
- `PREFETCH_COMPLETED`

## Related

- `frontend/src/lib/staleTimes.ts` — stale times per domain
- `docs/performance/frontend-optimization.md` — broader frontend perf notes
