import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

/**
 * Fetch up to 500 historical jobs from MongoDB (debug only).
 * @returns {Promise<Array<Record<string, unknown>>>}
 */
export async function fetchHistoricalJobs() {
  const response = await apiFetch(`/jobs/history`)

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return response.json()
}
