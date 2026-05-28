import { useEffect } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { scheduleHubTabPrefetch, type HubId } from "@/lib/hubTabPrefetch"

export type { HubId }

/**
 * Staggered background prefetch for sibling tabs in a grouped hub.
 */
export function useHubTabPrefetch(hub: HubId, activeTab: string) {
  const queryClient = useQueryClient()

  useEffect(() => {
    scheduleHubTabPrefetch(queryClient, hub, activeTab)
  }, [queryClient, hub, activeTab])
}
