/** Shared staleTime values (ms) for React Query caches. */

export const STALE_TIMES = {
  jobsFeed: 45_000,
  scanAnalytics: 60_000,
  dashboardCore: 45_000,
  dashboardInsights: 120_000,
  careerAnalytics: 120_000,
  scanCenter: 45_000,
} as const
