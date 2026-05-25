import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

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

  const response = await apiFetch(`/match-job`, {
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
