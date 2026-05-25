import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"

export async function getBrowserHealth() {
  const response = await apiFetch(`/automation/browser-health`)
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function getSessionStatus() {
  const response = await apiFetch(`/automation/session-status`)
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

/**
 * @param {{ url: string, platform?: string, headless?: boolean | null }} payload
 */
export async function testOpenUrl(payload) {
  const response = await apiFetch(`/automation/test-open`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return data
}

export async function testPlatformSession(platform) {
  const response = await apiFetch(
    `/automation/test-session/${encodeURIComponent(platform)}`,
    { method: "POST" }
  )
  const data = await response.json()
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "object"
        ? data.detail.message
        : await parseErrorMessage(response)
    )
  }
  return data
}

/**
 * Call while prepare-session or open-session is waiting (headed browser open).
 * @param {"prepare" | "open"} mode
 */
export async function signalManualSessionDone(platform, mode = "prepare") {
  const segment =
    mode === "open" ? "open-session" : "test-session"
  const response = await apiFetch(
    `/automation/${segment}/${encodeURIComponent(platform)}/done`,
    { method: "POST" }
  )
  const data = await response.json()
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return data
}

/** @deprecated use signalManualSessionDone(platform, "prepare") */
export async function signalPrepareSessionDone(platform) {
  return signalManualSessionDone(platform, "prepare")
}

export async function openPlatformSession(platform) {
  const response = await apiFetch(
    `/automation/open-session/${encodeURIComponent(platform)}`,
    { method: "POST" }
  )
  const data = await response.json()
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "object"
        ? data.detail.message
        : await parseErrorMessage(response)
    )
  }
  return data
}

export async function fetchLinkedInDiscovery() {
  const response = await apiFetch(`/automation/linkedin-discovery`, {
    method: "POST",
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return data
}

export async function deletePlatformSession(platform) {
  const response = await apiFetch(
    `/automation/session/${encodeURIComponent(platform)}`,
    { method: "DELETE" }
  )
  const data = await response.json()
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return data
}

/**
 * @param {string} relativePath e.g. logs/screenshots/generic/...
 */
export function screenshotUrl(relativePath) {
  if (!relativePath) return ""
  const normalized = relativePath.replace(/\\/g, "/")
  return `${getApiBaseUrl()}/automation/screenshot/${normalized}`
}
