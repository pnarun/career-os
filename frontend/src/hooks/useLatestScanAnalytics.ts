import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { trackFetch, trackFetchDuration } from "@/lib/perfDiagnostics"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getLatestScanAnalytics } from "@/services/scanAnalyticsService"

export function useLatestScanAnalytics({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.jobs.latestScan(),
    queryFn: async () => {
      trackFetch("scan-analytics.latest")
      const started = Date.now()
      try {
        return await getLatestScanAnalytics()
      } finally {
        trackFetchDuration("scan-analytics.latest", started)
      }
    },
    enabled,
    staleTime: STALE_TIMES.scanAnalytics,
  })
}
