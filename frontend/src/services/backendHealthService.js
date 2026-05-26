import { getApiBaseUrl } from "@/lib/apiClient"

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

/**
 * Ping /health — no auth required. Returns true when API responds ok/degraded.
 */
export async function pingBackendHealth(timeoutMs = 15000) {
  const base = getApiBaseUrl()
  if (!base) {
    return import.meta.env.DEV
  }

  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${base}/health`, {
      method: "GET",
      signal: controller.signal,
      cache: "no-store",
    })
    if (!response.ok) return false
    const data = await response.json()
    return data.status === "ok" || data.status === "degraded"
  } catch {
    return false
  } finally {
    window.clearTimeout(timer)
  }
}

/** Retry until backend is warm or attempts exhausted. */
export async function waitForBackendReady({
  maxAttempts = 40,
  intervalMs = 2000,
} = {}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    if (await pingBackendHealth()) return true
    if (attempt < maxAttempts - 1) {
      await sleep(intervalMs)
    }
  }
  return false
}

/** Fire-and-forget wake ping (landing page). */
export function wakeBackend() {
  void pingBackendHealth(20000)
}
