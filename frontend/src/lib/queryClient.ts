import { QueryClient } from "@tanstack/react-query"

import { STALE_TIMES } from "@/lib/staleTimes"

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: STALE_TIMES.jobsFeed,
      gcTime: 10 * 60_000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: 1,
    },
  },
})
