import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

/**
 * @param {Response} response
 */
/**
 * @param {Record<string, unknown>} job
 */
export function jobToApplicationPayload(job) {
  return {
    job_id: String(job.id || job.job_id || ""),
    title: String(job.title || ""),
    company: String(job.company || ""),
    source: String(job.source || ""),
    apply_url: String(job.apply_url || ""),
    match_score: Number(job.match_percentage ?? job.match_score ?? 0),
    remote: Boolean(job.remote_priority || job.remote || job.job_type === "remote"),
    easy_apply: Boolean(job.easy_apply || job.is_easy_apply_possible),
    location: String(job.location || ""),
    matched_skills: Array.isArray(job.matched_skills) ? job.matched_skills : [],
    notes: "",
  }
}

export async function saveJobApplication(job) {
  const response = await apiFetch(`/applications/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobToApplicationPayload(job)),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function markJobApplied(job) {
  const response = await apiFetch(`/applications/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobToApplicationPayload(job)),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

/**
 * @param {string} applicationId
 * @param {string} status
 */
export async function updateApplicationStatus(applicationId, status) {
  const response = await apiFetch(`/applications/${applicationId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

/**
 * @param {string} applicationId
 * @param {string} notes
 */
export async function updateApplicationNotes(applicationId, notes) {
  const response = await apiFetch(`/applications/${applicationId}/notes`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

/**
 * @param {Record<string, unknown>} [filters]
 */
export async function getApplications(filters = {}) {
  const params = new URLSearchParams()
  if (filters.status) params.set("status", filters.status)
  if (filters.source) params.set("source", filters.source)
  if (filters.remote != null) params.set("remote", String(filters.remote))
  if (filters.minMatch != null) params.set("min_match", String(filters.minMatch))
  if (filters.dateFrom) params.set("date_from", filters.dateFrom)
  if (filters.dateTo) params.set("date_to", filters.dateTo)
  if (filters.jobId) params.set("job_id", filters.jobId)

  const query = params.toString()
  const response = await apiFetch(`/applications${query ? `?${query}` : ""}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getApplicationAnalytics() {
  const response = await apiFetch(`/applications/analytics`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

/**
 * @param {string} [applicationId]
 */
export async function getApplicationTimeline(applicationId) {
  const params = applicationId ? `?application_id=${encodeURIComponent(applicationId)}` : ""
  const response = await apiFetch(`/applications/timeline${params}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  const data = await response.json()
  return data.events ?? []
}

export async function deleteApplication(applicationId) {
  const response = await apiFetch(`/applications/${applicationId}`, {
    method: "DELETE",
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export const APPLICATION_STATUSES = [
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interview", label: "Interview" },
  { value: "assessment", label: "Assessment" },
  { value: "rejected", label: "Rejected" },
  { value: "offer", label: "Offer" },
  { value: "ghosted", label: "Ghosted" },
  { value: "withdrawn", label: "Withdrawn" },
]

export const STATUS_TABS = [
  { id: "saved", label: "Saved Jobs", statuses: ["saved"] },
  { id: "applied", label: "Applied", statuses: ["applied"] },
  { id: "interviews", label: "Interviews", statuses: ["interview", "assessment"] },
  { id: "rejections", label: "Rejections", statuses: ["rejected", "ghosted"] },
  { id: "offers", label: "Offers", statuses: ["offer", "withdrawn"] },
]
