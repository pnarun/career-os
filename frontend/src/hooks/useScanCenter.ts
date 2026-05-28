import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { trackFetch, trackFetchDuration } from "@/lib/perfDiagnostics"
import { STALE_TIMES } from "@/lib/staleTimes"
import { loadScanCenterData } from "@/services/scansService"

export function useScanCenter({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.scans.center(),
    queryFn: async () => {
      trackFetch("scans.center")
      const started = Date.now()
      try {
        return await loadScanCenterData()
      } finally {
        trackFetchDuration("scans.center", started)
      }
    },
    enabled,
    staleTime: STALE_TIMES.scanCenter,
    placeholderData: (previous) => previous,
  })
}
