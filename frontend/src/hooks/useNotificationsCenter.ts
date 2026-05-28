import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { STALE_TIMES } from "@/lib/staleTimes"
import {
  getAutomationAnalytics,
  getCareerInsights,
  getNotifications,
} from "@/services/notificationService"

async function loadNotificationsCenter(tab: string) {
  const typeFilter = tab === "all" ? undefined : tab
  const [notifData, insightData, analyticsData] = await Promise.all([
    getNotifications({ type: typeFilter, limit: 100 }),
    getCareerInsights(10),
    getAutomationAnalytics(5),
  ])
  return {
    notifications: notifData.notifications ?? [],
    insights: insightData ?? [],
    analytics: analyticsData,
  }
}

export function useNotificationsCenter(activeTab: string) {
  return useQuery({
    queryKey: queryKeys.operations.notifications(activeTab),
    queryFn: () => loadNotificationsCenter(activeTab),
    staleTime: STALE_TIMES.scanCenter,
    placeholderData: (previous) => previous,
  })
}
