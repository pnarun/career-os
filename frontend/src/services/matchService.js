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
 * Match a resume against a job description.
 *
 * @param {{ resumeId?: string, jobDescription: string }} params
 * @returns {Promise<Record<string, unknown>>}
 */
export async function matchJob({ resumeId = "", jobDescription }) {
  if (!jobDescription?.trim() || jobDescription.trim().length < 10) {
    throw new Error("Job description must be at least 10 characters.")
  }

  const response = await fetch(`${API_BASE_URL}/match-job`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: resumeId.trim(),
      job_description: jobDescription.trim(),
    }),
  })

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return response.json()
}
