import { apiFetch, parseErrorMessage } from "@/lib/apiClient"
import { waitForScanCompletion } from "@/lib/scanRealtime"
import { realtimeClient } from "@/lib/realtimeClient"

const DEFAULT_POLL_MS = 3000
const MIN_POLL_MS = 1500
const MAX_POLL_MS = 5000

/** @type {Map<string, Promise<Record<string, unknown>>>} */
const activePolls = new Map()

function sleep(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Aborted", "AbortError"))
      return
    }
    const timer = window.setTimeout(resolve, ms)
    signal?.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timer)
        reject(new DOMException("Aborted", "AbortError"))
      },
      { once: true }
    )
  })
}

function resolvePollInterval(status, baseMs = DEFAULT_POLL_MS) {
  const pct = Number(status?.progress ?? 0)
  if (realtimeClient.isOpen()) {
    return Math.max(10_000, baseMs * 3)
  }
  if (pct >= 85) return Math.max(MIN_POLL_MS, Math.min(MAX_POLL_MS, baseMs + 1500))
  if (pct >= 50) return Math.max(MIN_POLL_MS, baseMs)
  return Math.max(MIN_POLL_MS, baseMs - 500)
}

/**
 * Start a background scan; returns immediately with scan_id.
 * @param {{ resume_id?: string, preferences_id?: string, send_email?: boolean }} body
 */
export async function startBackgroundScan(body = {}) {
  const response = await apiFetch("/scans/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function getBackgroundScanStatus(scanId) {
  const response = await apiFetch(`/scans/status/${encodeURIComponent(scanId)}`)
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

/**
 * Poll until scan completes or fails. Uses WebSocket when connected, else HTTP polling.
 * @param {string} scanId
 * @param {{
 *   intervalMs?: number
 *   onProgress?: (status: Record<string, unknown>) => void
 *   signal?: AbortSignal
 *   preferRealtime?: boolean
 * }} options
 */
export async function pollScanUntilComplete(
  scanId,
  { intervalMs = DEFAULT_POLL_MS, onProgress, signal, preferRealtime = true } = {}
) {
  const existing = activePolls.get(scanId)
  if (existing) return existing

  if (preferRealtime && (realtimeClient.isOpen() || realtimeClient.shouldConnect)) {
    const run = waitForScanCompletion(scanId, { onProgress, signal, preferRealtime: true })
    activePolls.set(scanId, run)
    try {
      return await run
    } finally {
      activePolls.delete(scanId)
    }
  }

  const run = (async () => {
    try {
      for (;;) {
        if (signal?.aborted) {
          throw new DOMException("Aborted", "AbortError")
        }

        const status = await getBackgroundScanStatus(scanId)
        onProgress?.(status)

        if (status.status === "completed") {
          return status
        }
        if (status.status === "failed") {
          const msg = (status.errors || []).join("; ") || "Scan failed"
          throw new Error(msg)
        }

        const waitMs = resolvePollInterval(status, intervalMs)
        await sleep(waitMs, signal)
      }
    } finally {
      activePolls.delete(scanId)
    }
  })()

  activePolls.set(scanId, run)
  return run
}

export function cancelActiveScanPoll(scanId) {
  activePolls.delete(scanId)
}

export function formatScanProgress(status) {
  if (!status) return "Starting scan…"
  const provider = status.current_provider
  const pct = status.progress ?? 0
  if (provider) {
    return `Scanning ${provider}… ${pct}%`
  }
  if (status.status === "processing") {
    return `Matching and ranking jobs… ${pct}%`
  }
  if (status.status === "fetching") {
    return `Fetching from job boards… ${pct}%`
  }
  return `Scan in progress… ${pct}%`
}
