import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

/**
 * Fetch up to 500 historical jobs from MongoDB (debug only).
 * @returns {Promise<Array<Record<string, unknown>>>}
 */
export async function fetchHistoricalJobs({ page = 1, limit = 100 } = {}) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  })
  const response = await apiFetch(`/jobs/history?${params}`)

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  const data = await response.json()
  return Array.isArray(data) ? data : data.items ?? []
}
