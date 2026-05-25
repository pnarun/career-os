import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"

export async function getResumeAiOverview(resumeId = "") {
  const params = resumeId ? `?resume_id=${encodeURIComponent(resumeId)}` : ""
  const response = await apiFetch(`/resume-ai/overview${params}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getAtsScore(resumeId = "", jobDescription = "") {
  const params = new URLSearchParams()
  if (resumeId) params.set("resume_id", resumeId)
  if (jobDescription) params.set("job_description", jobDescription)
  const qs = params.toString() ? `?${params}` : ""
  const response = await apiFetch(`/resume-ai/ats-score${qs}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function tailorResumeForJob(payload) {
  const response = await apiFetch(`/resume-ai/tailor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function alignResumeToJob(payload) {
  const response = await apiFetch(`/resume-ai/align-job`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function exportResume(payload) {
  const response = await apiFetch(`/resume-ai/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export function downloadExportResult(result) {
  if (result.content) {
    const blob = new Blob([result.content], { type: result.content_type })
    triggerDownload(blob, result.filename)
    return
  }
  if (result.data_base64) {
    const binary = atob(result.data_base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
    const blob = new Blob([bytes], { type: result.content_type })
    triggerDownload(blob, result.filename)
  }
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

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
