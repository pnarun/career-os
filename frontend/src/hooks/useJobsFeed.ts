import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { trackFetch, trackFetchDuration } from "@/lib/perfDiagnostics"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getJobsFeed } from "@/services/jobFeedService"

export type JobsFeedFilters = {
  providers?: string[]
  remoteOnly?: boolean
  easyApplyOnly?: boolean
  minMatch?: number
  keyword?: string
  sort?: string
  strongMatchesOnly?: boolean
  remoteHighMatch?: boolean
  easyApplyHighMatch?: boolean
  company?: string
}

export function useJobsFeed(filters: JobsFeedFilters, { enabled = true } = {}) {
  const stableFilters = {
    providers: filters.providers ?? [],
    remoteOnly: Boolean(filters.remoteOnly),
    easyApplyOnly: Boolean(filters.easyApplyOnly),
    minMatch: filters.minMatch ?? 0,
    keyword: filters.keyword ?? "",
    sort: filters.sort ?? "default",
    strongMatchesOnly: Boolean(filters.strongMatchesOnly),
    remoteHighMatch: Boolean(filters.remoteHighMatch),
    easyApplyHighMatch: Boolean(filters.easyApplyHighMatch),
    company: filters.company ?? "",
  }

  return useQuery({
    queryKey: queryKeys.jobs.feed(stableFilters),
    queryFn: async () => {
      const key = queryKeys.jobs.feed(stableFilters)
      trackFetch("jobs.feed", key)
      const started = Date.now()
      try {
        return await getJobsFeed({
          providers: stableFilters.providers,
          remoteOnly: stableFilters.remoteOnly,
          easyApplyOnly: stableFilters.easyApplyOnly,
          minMatch: stableFilters.minMatch > 0 ? stableFilters.minMatch : undefined,
          keyword: stableFilters.keyword,
          sort: stableFilters.sort,
          strongMatchesOnly: stableFilters.strongMatchesOnly,
          remoteHighMatch: stableFilters.remoteHighMatch,
          easyApplyHighMatch: stableFilters.easyApplyHighMatch,
          company: stableFilters.company || undefined,
        })
      } finally {
        trackFetchDuration("jobs.feed", started)
      }
    },
    enabled,
    staleTime: STALE_TIMES.jobsFeed,
    placeholderData: (previous) => previous,
  })
}
