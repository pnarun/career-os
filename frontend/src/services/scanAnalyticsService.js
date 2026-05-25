import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"

/**
 * @param {Response} response
 * @returns {Promise<string>}
 */
/**
 * @returns {Promise<Record<string, unknown> | null>}
 */
export async function getLatestScanAnalytics() {
  const response = await apiFetch(`/scan-analytics/latest`)
  if (response.status === 404) return null
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  const data = await response.json()
  return data ?? null
}
