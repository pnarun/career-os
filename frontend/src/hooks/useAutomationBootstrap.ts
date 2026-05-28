import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { STALE_TIMES } from "@/lib/staleTimes"
import {
  getLinkedInAutomationStatus,
  getSessionStatus,
} from "@/services/automationService"

async function loadAutomationBootstrap() {
  const [sessionRes, linkedinRes] = await Promise.all([
    getSessionStatus(),
    getLinkedInAutomationStatus(),
  ])
  return {
    sessions: sessionRes.sessions ?? {},
    linkedin: linkedinRes,
  }
}

export function useAutomationBootstrap({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.operations.automationBootstrap(),
    queryFn: loadAutomationBootstrap,
    enabled,
    staleTime: STALE_TIMES.scanCenter,
    placeholderData: (previous) => previous,
  })
}
