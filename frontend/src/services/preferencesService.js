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
 * @param {Record<string, unknown>} payload
 * @returns {Promise<Record<string, unknown>>}
 */
export async function savePreferences(payload) {
  const response = await fetch(`${API_BASE_URL}/preferences`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

/**
 * @returns {Promise<Record<string, unknown> | null>}
 */
export async function getPreferences() {
  const response = await fetch(`${API_BASE_URL}/preferences`)

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  const data = await response.json()
  return data ?? null
}

/**
 * @param {string} preferenceId
 * @param {Record<string, unknown>} payload
 * @returns {Promise<Record<string, unknown>>}
 */
export async function updatePreferences(preferenceId, payload) {
  const params = new URLSearchParams({ preference_id: preferenceId })
  const response = await fetch(`${API_BASE_URL}/preferences?${params}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

/**
 * @returns {Promise<Array<Record<string, unknown>>>}
 */
export async function listResumes() {
  const response = await fetch(`${API_BASE_URL}/resumes`)

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

/**
 * @param {string} preferencesId
 * @returns {Promise<Record<string, unknown>>}
 */
export async function runScanNow(preferencesId) {
  const response = await fetch(`${API_BASE_URL}/run-scan-now`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences_id: preferencesId }),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

/**
 * @param {string} [resumeId]
 * @returns {Promise<{ preview_html: string, jobs_count: number, scan_id?: string, scan_timestamp?: string }>}
 */
export async function getEmailPreview(resumeId) {
  const params = new URLSearchParams()
  if (resumeId) {
    params.set("resume_id", resumeId)
  }

  const query = params.toString()
  const url = `${API_BASE_URL}/email-preview${query ? `?${query}` : ""}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

/**
 * @param {string} preferencesId
 * @returns {Promise<Record<string, unknown>>}
 */
export async function sendEmailNow(preferencesId) {
  const response = await fetch(`${API_BASE_URL}/send-email-now`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences_id: preferencesId }),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}
