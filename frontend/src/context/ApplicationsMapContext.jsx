import { createContext, useCallback, useContext, useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/apiClient"

const ApplicationsMapContext = createContext(null)

async function fetchJobApplicationMap() {
  const response = await apiFetch("/applications/job-map")
  if (!response.ok) return {}
  return response.json()
}

export function ApplicationsMapProvider({ children }) {
  const queryClient = useQueryClient()
  const [localOverrides, setLocalOverrides] = useState({})

  const { data: serverMap = {}, isLoading } = useQuery({
    queryKey: ["applications", "job-map"],
    queryFn: fetchJobApplicationMap,
    staleTime: 60_000,
  })

  const applicationByJobId = useMemo(
    () => ({ ...serverMap, ...localOverrides }),
    [serverMap, localOverrides]
  )

  const setApplicationForJob = useCallback((jobId, application) => {
    if (!jobId) return
    setLocalOverrides((prev) => ({
      ...prev,
      [String(jobId)]: application,
    }))
    queryClient.setQueryData(["applications", "job-map"], (old) => ({
      ...(old || {}),
      [String(jobId)]: application,
    }))
  }, [queryClient])

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["applications", "job-map"] })
  }, [queryClient])

  const value = useMemo(
    () => ({
      applicationByJobId,
      isLoading,
      setApplicationForJob,
      invalidate,
    }),
    [applicationByJobId, isLoading, setApplicationForJob, invalidate]
  )

  return (
    <ApplicationsMapContext.Provider value={value}>
      {children}
    </ApplicationsMapContext.Provider>
  )
}

export function useApplicationsMap() {
  const ctx = useContext(ApplicationsMapContext)
  if (!ctx) {
    throw new Error("useApplicationsMap must be used within ApplicationsMapProvider")
  }
  return ctx
}

export function useApplicationsMapOptional() {
  return useContext(ApplicationsMapContext)
}
