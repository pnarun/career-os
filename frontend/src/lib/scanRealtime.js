import { realtimeClient } from "@/lib/realtimeClient"
import { getBackgroundScanStatus } from "@/services/scanBackgroundService"

const TERMINAL_EVENTS = new Set(["scan_completed", "scan_failed"])
const PROGRESS_EVENTS = new Set([
  "scan_started",
  "scan_progress",
  "provider_started",
  "provider_completed",
  "jobs_fetched",
  "ai_scoring_complete",
])

/**
 * Map websocket payload into scan status shape used by Jobs/Scans UI.
 * @param {Record<string, unknown>} payload
 */
export function wsPayloadToScanStatus(payload) {
  if (!payload?.scan_id) return null
  const providers = payload.providers || {}
  return {
    scan_id: payload.scan_id,
    status: payload.status || (payload.event === "scan_completed" ? "completed" : payload.event === "scan_failed" ? "failed" : "fetching"),
    progress: payload.progress ?? 0,
    current_provider: payload.current_provider || payload.provider || "",
    providers,
    providers_completed: payload.providers_completed || [],
    providers_failed: payload.providers_failed || [],
    jobs_found: payload.jobs_found ?? 0,
    jobs_stored: payload.jobs_stored ?? payload.stored ?? 0,
    errors: payload.errors || (payload.reason ? [payload.reason] : []),
    result_summary: payload.result_summary,
  }
}

/**
 * Wait for scan completion via WebSocket with slow HTTP polling fallback.
 * @param {string} scanId
 * @param {{
 *   onProgress?: (status: Record<string, unknown>) => void
 *   signal?: AbortSignal
 *   preferRealtime?: boolean
 * }} [options]
 */
export function waitForScanCompletion(scanId, { onProgress, signal, preferRealtime = true } = {}) {
  const existing = waitForScanCompletion._active?.get(scanId)
  if (existing) return existing

  const wsConnected = preferRealtime && realtimeClient.isOpen()
  const pollMs = wsConnected ? 12_000 : 3000

  const promise = new Promise((resolve, reject) => {
    let unsub = null
    let pollTimer = null
    let settled = false

    const cleanup = () => {
      if (unsub) unsub()
      unsub = null
      if (pollTimer) window.clearTimeout(pollTimer)
      pollTimer = null
      waitForScanCompletion._active?.delete(scanId)
    }

    const finish = (status) => {
      if (settled) return
      settled = true
      cleanup()
      resolve(status)
    }

    const fail = (err) => {
      if (settled) return
      settled = true
      cleanup()
      reject(err)
    }

    const handleStatus = (status) => {
      if (!status) return
      onProgress?.(status)
      if (status.status === "completed") finish(status)
      if (status.status === "failed") {
        const msg = (status.errors || []).join("; ") || "Scan failed"
        fail(new Error(msg))
      }
    }

    const pollOnce = async () => {
      if (signal?.aborted) {
        fail(new DOMException("Aborted", "AbortError"))
        return
      }
      try {
        const status = await getBackgroundScanStatus(scanId)
        handleStatus(status)
        if (!settled) {
          pollTimer = window.setTimeout(pollOnce, pollMs)
        }
      } catch (err) {
        fail(err)
      }
    }

    if (wsConnected) {
      unsub = realtimeClient.subscribe((payload) => {
        if (payload.scan_id !== scanId) return
        if (PROGRESS_EVENTS.has(payload.event) || TERMINAL_EVENTS.has(payload.event)) {
          handleStatus(wsPayloadToScanStatus(payload))
        }
        if (payload.event === "scan_completed") {
          getBackgroundScanStatus(scanId)
            .then((status) => finish(status))
            .catch(() =>
              finish(
                wsPayloadToScanStatus(payload) || {
                  scan_id: scanId,
                  status: "completed",
                  result_summary: payload.result_summary,
                }
              )
            )
        }
        if (payload.event === "scan_failed") {
          fail(new Error(payload.reason || payload.message || "Scan failed"))
        }
      })
    }

    pollOnce()
  })

  if (!waitForScanCompletion._active) {
    waitForScanCompletion._active = new Map()
  }
  waitForScanCompletion._active.set(scanId, promise)
  return promise
}
