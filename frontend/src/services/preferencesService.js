import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

export async function savePreferences(payload) {
  const response = await apiFetch("/preferences", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function getPreferences() {
  const response = await apiFetch("/preferences")

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  const data = await response.json()
  return data ?? null
}

export async function updatePreferences(preferenceId, payload) {
  const params = new URLSearchParams({ preference_id: preferenceId })
  const response = await apiFetch(`/preferences?${params}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function listResumes() {
  const response = await apiFetch("/resumes")

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function runScanNow(preferencesId) {
  const response = await apiFetch("/run-scan-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences_id: preferencesId }),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function sendEmailNow(preferencesId) {
  const response = await apiFetch("/send-email-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences_id: preferencesId }),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function getEmailPreview(resumeId) {
  const params = resumeId ? `?resume_id=${encodeURIComponent(resumeId)}` : ""
  const response = await apiFetch(`/email-preview${params}`)

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}
