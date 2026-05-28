/** Dev-only prefetch instrumentation (see docs/performance/prefetching-strategy.md). */

export function logPrefetch(
  event: "PREFETCH_STARTED" | "PREFETCH_SKIPPED_CACHE_HIT" | "PREFETCH_COMPLETED",
  key: readonly unknown[],
  detail?: string
) {
  if (!import.meta.env.DEV) return
  const label = JSON.stringify(key)
  if (detail) {
    console.debug(`[prefetch] ${event}`, label, detail)
  } else {
    console.debug(`[prefetch] ${event}`, label)
  }
}
