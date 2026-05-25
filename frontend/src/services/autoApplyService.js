import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"

/** Disabled by default. Set VITE_ASSISTED_APPLY_ENABLED=true in .env to re-enable. */
export const ASSISTED_APPLY_ENABLED =
  import.meta.env.VITE_ASSISTED_APPLY_ENABLED === "true"

export const APPLY_STATES = {
  IDLE: "Starting",
  OPENING_JOB: "Opening job",
  DETECTING_FORM: "Detecting form",
  UPLOADING_RESUME: "Uploading resume",
  FILLING_FIELDS: "Filling fields",
  DETECTING_QUESTIONS: "Detecting questions",
  WAITING_CONFIRMATION: "Awaiting your confirmation",
  SUBMITTING: "Submitting",
  SUCCESS: "Application submitted",
  FAILED: "Failed",
  CAPTCHA_BLOCKED: "CAPTCHA detected — manual action required",
  CANCELLED: "Cancelled",
}

export function jobToApplyPayload(job) {
  return {
    job_id: String(job.id || job.job_id || ""),
    job_url: String(job.apply_url || job.url || ""),
    title: String(job.title || ""),
    company: String(job.company || ""),
    source: String(job.source || job.provider || "").toLowerCase(),
    resume_id: String(job.resume_id || ""),
    match_score: Number(job.match_score ?? job.match_percentage ?? 0),
  }
}

export async function getApplyLimits() {
  const response = await apiFetch(`/auto-apply/analytics/limits`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function startAssistedApply(payload) {
  const response = await apiFetch(`/auto-apply/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getApplySession(sessionId) {
  const response = await apiFetch(`/auto-apply/${sessionId}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function confirmAssistedApply(sessionId, answers = {}) {
  const response = await apiFetch(`/auto-apply/${sessionId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function cancelAssistedApply(sessionId) {
  const response = await apiFetch(`/auto-apply/${sessionId}/cancel`, {
    method: "POST",
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export function screenshotUrl(relativePath) {
  if (!relativePath) return ""
  return `${getApiBaseUrl()}/automation/screenshot/${relativePath}`
}

export function isLinkedInEasyApply(job) {
  const source = String(job.source || job.provider || "").toLowerCase()
  return source === "linkedin" && Boolean(job.easy_apply || job.is_easy_apply_possible)
}

export function pollApplySession(sessionId, { intervalMs = 2000, onUpdate, onTerminal }) {
  let active = true

  const tick = async () => {
    if (!active) return
    try {
      const session = await getApplySession(sessionId)
      onUpdate?.(session)
      const terminal = ["SUCCESS", "FAILED", "CAPTCHA_BLOCKED", "CANCELLED"]
      if (terminal.includes(session.state)) {
        onTerminal?.(session)
        active = false
        return
      }
    } catch {
      /* keep polling */
    }
    if (active) setTimeout(tick, intervalMs)
  }

  tick()
  return () => {
    active = false
  }
}
