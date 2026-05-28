import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getResumeAiOverview } from "@/services/resumeAiService"

export function useResumeAiOverview(resumeId = "", { enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.resume.aiOverview(resumeId),
    queryFn: () => getResumeAiOverview(resumeId),
    enabled,
    staleTime: STALE_TIMES.dashboardInsights,
    placeholderData: (previous) => previous,
  })
}
