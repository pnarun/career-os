import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

export function scoreColor(score) {
  if (score >= 85) return "text-emerald-400"
  if (score >= 70) return "text-sky-400"
  if (score >= 50) return "text-amber-400"
  return "text-red-400"
}

export function scoreRingColor(score) {
  if (score >= 85) return "#34d399"
  if (score >= 70) return "#38bdf8"
  if (score >= 50) return "#fbbf24"
  return "#f87171"
}

export async function getInterviewPrepJobs(filter = "all") {
  const response = await apiFetch(
    `/interview-prep/jobs?filter=${encodeURIComponent(filter)}`
  )
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getInterviewPrepOverview(params = {}) {
  const qs = new URLSearchParams()
  if (params.job_id) qs.set("job_id", params.job_id)
  if (params.job_description) qs.set("job_description", params.job_description)
  if (params.job_title) qs.set("job_title", params.job_title)
  if (params.company) qs.set("company", params.company)
  const query = qs.toString() ? `?${qs}` : ""
  const response = await apiFetch(`/interview-prep/overview${query}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function startMockInterview(payload) {
  const response = await apiFetch(`/interview-prep/mock/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function completeMockSession(payload) {
  const response = await apiFetch(`/interview-prep/mock/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function recordPractice(payload) {
  const response = await apiFetch(`/interview-prep/practice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function markTopicComplete(payload) {
  const response = await apiFetch(`/interview-prep/topic-complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export function jobToInterviewPayload(job) {
  return {
    job_id: String(job.id || job.job_id || ""),
    job_description: String(job.description || ""),
    job_title: String(job.title || ""),
    company: String(job.company || ""),
  }
}
