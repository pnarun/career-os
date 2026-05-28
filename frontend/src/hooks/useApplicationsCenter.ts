import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import { STALE_TIMES } from "@/lib/staleTimes"
import { getApplicationAnalytics, getApplications } from "@/services/applicationService"

export const DEFAULT_APPLICATIONS_FILTERS = {
  status: "",
  source: "",
  remote: false,
  minMatch: 0,
}

export type ApplicationsFilters = {
  status?: string
  source?: string
  remote?: boolean
  minMatch?: number
}

async function loadApplicationsCenter(filters: ApplicationsFilters) {
  const [applications, analytics] = await Promise.all([
    getApplications({
      status: filters.status || undefined,
      source: filters.source || undefined,
      remote: filters.remote ? true : undefined,
      minMatch: (filters.minMatch ?? 0) > 0 ? filters.minMatch : undefined,
    }),
    getApplicationAnalytics(),
  ])
  return { applications, analytics }
}

export function useApplicationsCenter(filters: ApplicationsFilters) {
  const stable = {
    status: filters.status ?? "",
    source: filters.source ?? "",
    remote: Boolean(filters.remote),
    minMatch: filters.minMatch ?? 0,
  }

  return useQuery({
    queryKey: queryKeys.career.applications(stable),
    queryFn: () => loadApplicationsCenter(stable),
    staleTime: STALE_TIMES.scanCenter,
    placeholderData: (previous) => previous,
  })
}
