# Frontend performance optimization

Career OS frontend optimizations focus on **caching**, **pagination**, **code splitting**, and **smaller in-memory payloads**—without changing product behavior or API contracts.

## React Query caching

TanStack Query is configured in `frontend/src/lib/queryClient.ts` with shared `staleTime` values from `frontend/src/lib/staleTimes.ts`.

| Query | Key | staleTime |
|-------|-----|-----------|
| Jobs feed | `queryKeys.jobs.feed(filters)` | 45s |
| Latest scan analytics | `queryKeys.jobs.latestScan()` | 60s |
| Dashboard core | `queryKeys.dashboard.core()` | 45s |
| Dashboard insights | `queryKeys.dashboard.insights()` | 120s |
| Career analytics | `queryKeys.analytics.career(role)` | 120s |
| Scan center | `queryKeys.scans.center()` | 45s |

Hooks live under `frontend/src/hooks/` (`useJobsFeed`, `useLatestScanAnalytics`, `useCareerAnalyticsDashboard`, `useScanCenter`).

**Invalidation:** `feedVersion` from realtime context invalidates `queryKeys.jobs.all` and `queryKeys.scans.center()` so remounts reuse cache instead of duplicating in-flight requests.

`placeholderData: (prev) => prev` on feed and analytics avoids UI flicker when filters or roles change.

## Jobs feed & list rendering

### Client pagination

`VirtualizedJobGrid` (name is historical) pages the filtered list with **`JOBS_PAGE_SIZE = 6`** and `JobListPagination.jsx`. Only six cards mount per page so variable card heights never overlap.

The grid is a normal responsive CSS grid (`grid-cols-1` → `xl:grid-cols-3`) with `self-start` on each card — **no `react-window`** on the jobs feed (removed after overlap issues with fixed row heights).

### List-view payload trimming

`mapFeedJobToDisplay(job, { listView: true })` stores a truncated `description` for cards and keeps the full text in `description_full` for the description modal and keyword search.

## Scan polling

`frontend/src/services/scanBackgroundService.js`:

- **Deduplicates** concurrent polls per `scan_id`
- **Adaptive intervals** (faster early, slower near completion)
- Supports **`AbortSignal`** for cancellation

## Route & tab code splitting

`App.tsx` lazy-loads main hubs. Additionally:

- `OperationsHub` lazy-loads Scans, Automation, Notifications per tab
- `InsightsHub` lazy-loads Career Analytics and Copilot

## Memoization

- `JobCard` — `memo`
- `StatCard` — `memo`
- Career analytics charts — `memo` wrappers in `CareerAnalyticsCharts.jsx`
- `KpiCard` in Career Analytics — `memo`

## Loading UX

- Dashboard — section skeletons (`SectionSkeleton`)
- Career Analytics — `AnalyticsPageSkeleton` (initial load); cached data stays visible on refresh
- Scan center — `SlowLoadingPageCenter` on first load only; spinner on manual refresh button

## Dev diagnostics

`frontend/src/lib/perfDiagnostics.ts` (dev builds only):

- Duplicate fetch warnings within 800ms
- Slow fetch warnings (>2.5s)
- Optional slow render warnings via `useRenderTiming`

## Rendering philosophy

1. **Fetch once, cache by key** — filter objects must be stable and serializable.
2. **Never render unbounded lists** — paginate the jobs feed; keep page size small enough for stable card layout.
3. **Trim what React holds** — full job descriptions only when modals need them.
4. **Split heavy routes** — analytics, automation, and scans load on demand.
5. **Stop polling when done** — no background poll loops after terminal scan state.

## Verification checklist

- [ ] Jobs page: filter changes do not double-fetch on remount (Network tab)
- [ ] Jobs list: pagination appears when >6 jobs; page change scrolls to top; cards do not overlap
- [ ] Dashboard: second visit within stale window serves from cache
- [ ] Analytics: role change uses cache/placeholder; refresh spins button only
- [ ] Scans: history table paginated; scan poll stops after complete/fail
- [ ] Navigation: Operations/Insights tabs load chunks on first open only

## Related docs

- [Redis caching](./redis-caching.md)
- [Background scans](./background-scans.md)
- [MongoDB optimization](./mongodb-optimization.md)
