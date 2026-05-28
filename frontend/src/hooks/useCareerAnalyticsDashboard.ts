import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { trackFetch, trackFetchDuration } from "@/lib/perfDiagnostics"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getCareerAnalyticsDashboard } from "@/services/careerAnalyticsService"

export function useCareerAnalyticsDashboard(role: string, { enabled = true } = {}) {
  const normalizedRole = role?.trim() ?? ""

  return useQuery({
    queryKey: queryKeys.analytics.career(normalizedRole),
    queryFn: async () => {
      trackFetch("career-analytics.dashboard", normalizedRole)
      const started = Date.now()
      try {
        return await getCareerAnalyticsDashboard(normalizedRole)
      } finally {
        trackFetchDuration("career-analytics.dashboard", started)
      }
    },
    enabled,
    staleTime: STALE_TIMES.careerAnalytics,
    placeholderData: (previous) => previous,
  })
}
