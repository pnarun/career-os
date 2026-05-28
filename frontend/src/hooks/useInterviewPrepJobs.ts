import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getInterviewPrepJobs } from "@/services/interviewAiService"

export function useInterviewPrepJobs(statusFilter = "all", { enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.career.interviewJobs(statusFilter),
    queryFn: async () => {
      const result = await getInterviewPrepJobs(statusFilter)
      return result.jobs ?? []
    },
    enabled,
    staleTime: STALE_TIMES.scanCenter,
    placeholderData: (previous) => previous,
  })
}
