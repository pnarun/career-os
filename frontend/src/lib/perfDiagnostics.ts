import { isDevBuild } from "@/lib/env"

const fetchCounts = new Map<string, number>()
const fetchTimestamps = new Map<string, number>()

const DUPLICATE_WINDOW_MS = 800

/**
 * Dev-only: log duplicate fetches and slow API calls.
 */
export function trackFetch(label: string, key?: unknown) {
  if (!isDevBuild) return

  const id = `${label}:${JSON.stringify(key ?? "")}`
  const now = Date.now()
  const last = fetchTimestamps.get(id)
  const count = (fetchCounts.get(id) ?? 0) + 1
  fetchCounts.set(id, count)
  fetchTimestamps.set(id, now)

  if (last != null && now - last < DUPLICATE_WINDOW_MS) {
    console.warn(`[perf] Duplicate fetch within ${DUPLICATE_WINDOW_MS}ms: ${label}`, key)
  }
}

export function trackFetchDuration(label: string, startedAt: number) {
  if (!isDevBuild) return
  const ms = Date.now() - startedAt
  if (ms > 2500) {
    console.warn(`[perf] Slow fetch (${ms}ms): ${label}`)
  }
}

/**
 * Dev-only: warn when a component render exceeds threshold.
 */
export function useRenderTiming(componentName: string, thresholdMs = 32) {
  if (!isDevBuild) return

  const start = performance.now()
  queueMicrotask(() => {
    const elapsed = performance.now() - start
    if (elapsed > thresholdMs) {
      console.warn(`[perf] Slow render (${Math.round(elapsed)}ms): ${componentName}`)
    }
  })
}
