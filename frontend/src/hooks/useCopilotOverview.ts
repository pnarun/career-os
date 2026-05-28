import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getCopilotHistory, getCopilotOverview } from "@/services/copilotService"

async function loadCopilotOverview() {
  const ov = await getCopilotOverview()
  const hist = await getCopilotHistory(10).catch(() => ({ history: [] }))
  return { overview: ov, history: hist.history ?? [] }
}

export function useCopilotOverview({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.insights.copilotOverview(),
    queryFn: loadCopilotOverview,
    enabled,
    staleTime: STALE_TIMES.dashboardInsights,
    placeholderData: (previous) => previous,
  })
}
