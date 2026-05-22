const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001"

/**
 * @param {Response} response
 * @returns {Promise<string>}
 */
async function parseErrorMessage(response) {
  try {
    const data = await response.json()
    const detail = data?.detail

    if (typeof detail === "string") {
      return detail
    }

    if (detail?.message) {
      return detail.message
    }

    return data?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

/**
 * Fetch up to 500 historical jobs from MongoDB (debug only).
 * @returns {Promise<Array<Record<string, unknown>>>}
 */
export async function fetchHistoricalJobs() {
  const response = await fetch(`${API_BASE_URL}/jobs/history`)

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return response.json()
}
