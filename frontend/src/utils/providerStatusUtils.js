/** @typedef {import('./jobLocationUtils').JobLike} JobLike */

export const PROVIDER_ERROR_LABELS = {
  none: "OK",
  network_failure: "Network failure",
  parsing_failure: "Parsing failure",
  auth_required: "Login / session required",
  rate_limit: "Rate limited",
  selector_mismatch: "Selector / schema mismatch",
  timeout: "Timeout",
  unknown: "Unknown error",
}

const STATUS_STYLES = {
  success: "border-green-500/40 bg-green-500/10 text-green-300",
  failed: "border-red-500/40 bg-red-500/10 text-red-300",
  empty: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  skipped: "border-border/60 bg-muted/30 text-muted-foreground",
}

/**
 * @param {string} errorType
 */
export function getProviderErrorLabel(errorType) {
  return PROVIDER_ERROR_LABELS[errorType] || PROVIDER_ERROR_LABELS.unknown
}

/**
 * @param {Record<string, unknown>} diagnostic
 */
export function getProviderStatusStyle(diagnostic) {
  const status = String(diagnostic?.status || "failed")
  return STATUS_STYLES[status] || STATUS_STYLES.failed
}

export const KNOWN_PROVIDERS = [
  "remoteok",
  "arbeitnow",
  "indeed",
  "naukri",
  "instahyre",
  "linkedin",
]

/**
 * @param {string} message
 */
export function inferErrorTypeFromMessage(message) {
  const text = (message || "").toLowerCase()
  if (!text) return "unknown"
  if (text.includes("timeout") || text.includes("timed out")) return "timeout"
  if (text.includes("429") || text.includes("rate limit") || text.includes("403")) {
    if (text.includes("session") || text.includes("login") || text.includes("cookie")) {
      return "auth_required"
    }
    return "rate_limit"
  }
  if (
    text.includes("session") ||
    text.includes("login") ||
    text.includes("401") ||
    text.includes("unauthorized")
  ) {
    return "auth_required"
  }
  if (text.includes("404") || text.includes("not found") || text.includes("connection")) {
    return "network_failure"
  }
  if (
    text.includes("parse") ||
    text.includes("xml") ||
    text.includes("json") ||
    text.includes("selector") ||
    text.includes("no job")
  ) {
    return text.includes("selector") || text.includes("no job")
      ? "selector_mismatch"
      : "parsing_failure"
  }
  return "unknown"
}

/**
 * Merge scan summary from fetch response, analytics API, and top-level fields.
 * @param {Record<string, unknown> | null} scanSummaryResponse
 * @param {Record<string, unknown> | null} scanAnalytics
 */
export function resolveScanSummary(scanSummaryResponse, scanAnalytics) {
  const nested = scanSummaryResponse?.scan_summary
  const base =
    (nested && typeof nested === "object" ? nested : null) ||
    scanAnalytics ||
    scanSummaryResponse

  if (!base || typeof base !== "object") return null

  const providerStatus =
    (Array.isArray(base.provider_status) && base.provider_status.length > 0
      ? base.provider_status
      : null) ||
    (Array.isArray(scanSummaryResponse?.provider_status) &&
    scanSummaryResponse.provider_status.length > 0
      ? scanSummaryResponse.provider_status
      : null) ||
    []

  const sourceErrors = {
    ...(typeof base.source_errors === "object" && base.source_errors
      ? base.source_errors
      : {}),
    ...(typeof scanSummaryResponse?.source_errors === "object" &&
    scanSummaryResponse.source_errors
      ? scanSummaryResponse.source_errors
      : {}),
  }

  const failedSources = base.failed_sources || scanSummaryResponse?.failed_sources || []

  return {
    ...base,
    sources: base.sources || scanSummaryResponse?.sources || {},
    failed_sources: failedSources,
    source_errors: sourceErrors,
    provider_status: providerStatus,
  }
}

/**
 * @param {Record<string, unknown> | null | undefined} summary
 */
export function getProviderStatusList(summary) {
  if (!summary) return []

  /** @type {Map<string, Record<string, unknown>>} */
  const bySource = new Map()

  for (const item of summary.provider_status || []) {
    if (item && item.source) {
      bySource.set(String(item.source), item)
    }
  }

  const sources = summary.sources || {}
  const sourceErrors = summary.source_errors || {}
  const failed = new Set(summary.failed_sources || [])

  for (const name of KNOWN_PROVIDERS) {
    if (bySource.has(name)) continue

    const jobsFetched = Number(sources[name] ?? 0)
    const errorMessage = String(
      sourceErrors[name] ||
        (failed.has(name) ? "Fetch failed — see backend logs for details" : "")
    )

    if (jobsFetched > 0 && !failed.has(name)) {
      bySource.set(name, {
        source: name,
        status: "success",
        jobs_fetched: jobsFetched,
        duration_ms: 0,
        error_type: "none",
        error_message: "",
        requires_auth: false,
        session_valid: null,
      })
      continue
    }

    if (failed.has(name) || errorMessage) {
      bySource.set(name, {
        source: name,
        status: "failed",
        jobs_fetched: jobsFetched,
        duration_ms: 0,
        error_type: inferErrorTypeFromMessage(errorMessage),
        error_message: errorMessage,
        requires_auth: errorMessage.toLowerCase().includes("session"),
        session_valid: null,
      })
      continue
    }

    bySource.set(name, {
      source: name,
      status: "skipped",
      jobs_fetched: 0,
      duration_ms: 0,
      error_type: "none",
      error_message: "Not included in this scan (run Fetch Jobs again)",
      requires_auth: false,
      session_valid: null,
    })
  }

  return KNOWN_PROVIDERS.map((name) => bySource.get(name)).filter(Boolean)
}
