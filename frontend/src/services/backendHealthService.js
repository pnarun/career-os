import { getApiBaseUrl } from "@/lib/apiClient"

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

/**
 * Fetch /health — no auth. Returns { ok, data, error }.
 * UptimeRobot-compatible: lightweight, includes scheduler status.
 */
export async function fetchBackendHealth(timeoutMs = 15000) {
  const base = getApiBaseUrl()
  if (!base) {
    return {
      ok: false,
      error: import.meta.env.DEV
        ? "No API URL (dev defaults to localhost)"
        : "VITE_API_BASE_URL is not set on Vercel",
    }
  }

  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${base}/health`, {
      method: "GET",
      signal: controller.signal,
      cache: "no-store",
    })
    if (!response.ok) {
      return { ok: false, error: `HTTP ${response.status}` }
    }
    const data = await response.json()
    const apiUp = data.status === "ok"
    const schedulerUp =
      data.scheduler === "running" || data.scheduler_running === true
    return { ok: apiUp, schedulerOk: schedulerUp, data }
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Network error",
    }
  } finally {
    window.clearTimeout(timer)
  }
}

/** @deprecated use fetchBackendHealth */
export async function pingBackendHealth(timeoutMs = 15000) {
  const result = await fetchBackendHealth(timeoutMs)
  return result.ok
}

/** Retry until backend is warm or attempts exhausted. */
export async function waitForBackendReady({
  maxAttempts = 40,
  intervalMs = 2000,
} = {}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const { ok } = await fetchBackendHealth()
    if (ok) return true
    if (attempt < maxAttempts - 1) {
      await sleep(intervalMs)
    }
  }
  return false
}

/** Fire-and-forget wake ping (landing page). */
export function wakeBackend() {
  void fetchBackendHealth(20000)
}
