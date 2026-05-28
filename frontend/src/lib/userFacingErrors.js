/**
 * Maps API / provider / automation errors to calm, user-facing copy.
 */

const PATTERNS = [
  {
    test: (t) =>
      t.includes("401") ||
      t.includes("unauthorized") ||
      (t.includes("session") && (t.includes("invalid") || t.includes("expired"))) ||
      t.includes("not ready") ||
      t.includes("prepare a session"),
    message:
      "Your LinkedIn session expired. Reconnect in Scans & Automation → Automation.",
  },
  {
    test: (t) => t.includes("timeout") || t.includes("timed out"),
    message:
      "LinkedIn is taking longer than expected. We'll keep trying in the background.",
  },
  {
    test: (t) => t.includes("selector") || t.includes("couldn't read") || t.includes("no job"),
    message:
      "We couldn't read LinkedIn jobs right now. Please retry in a few minutes.",
  },
  {
    test: (t) => t.includes("rate limit") || t.includes("429"),
    message: "LinkedIn is busy right now. Wait a few minutes, then try again.",
  },
  {
    test: (t) => t.includes("pairing") && t.includes("expired"),
    message: "That pairing code expired. Generate a new code and try again.",
  },
  {
    test: (t) => t.includes("pairing") && (t.includes("invalid") || t.includes("incorrect")),
    message: "That pairing code didn't match. Generate a fresh code in Career OS.",
  },
  {
    test: (t) => t.includes("network") || t.includes("fetch failed") || t.includes("econnrefused"),
    message: "We couldn't reach the server. Check your connection and try again.",
  },
  {
    test: (t) => t.includes("request failed (5"),
    message: "Something went wrong on our side. Please try again in a moment.",
  },
]

export const PROVIDER_USER_MESSAGES = {
  none: "",
  network_failure: "We couldn't reach this job source. We'll retry on the next scan.",
  parsing_failure: "We received jobs but had trouble reading the format. We'll retry soon.",
  auth_required:
    "Your LinkedIn session expired. Reconnect in Scans & Automation → Automation.",
  rate_limit: "This source is rate-limited. Your next scan will try again automatically.",
  selector_mismatch:
    "We couldn't read LinkedIn jobs right now. Please retry in a few minutes.",
  timeout:
    "LinkedIn is taking longer than expected. We'll keep trying in the background.",
  unknown: "This source had a temporary issue. Try running a scan again.",
}

/**
 * @param {unknown} raw
 * @param {string} [fallback]
 */
export function humanizeErrorMessage(raw, fallback = "Something went wrong. Please try again.") {
  const text = String(raw ?? "").trim()
  if (!text) return fallback
  const lower = text.toLowerCase()
  for (const { test, message } of PATTERNS) {
    if (test(lower)) return message
  }
  if (lower.startsWith("request failed (")) return fallback
  return text
}

/**
 * @param {string} errorType
 * @param {string} [rawMessage]
 */
export function getProviderUserMessage(errorType, rawMessage = "") {
  const key = errorType || "unknown"
  const mapped = PROVIDER_USER_MESSAGES[key]
  if (mapped) return mapped
  return humanizeErrorMessage(rawMessage, PROVIDER_USER_MESSAGES.unknown)
}

/** LinkedIn fetch API status payloads */
export function linkedInFetchUserMessage(data) {
  if (!data) return "LinkedIn import didn't complete. Please try again."
  const status = String(data.status || "")
  if (status === "ok" || status === "empty") {
    if (Number(data.jobs_stored) > 0) {
      return `Added ${data.jobs_stored} LinkedIn jobs to your feed.`
    }
    return data.message || "LinkedIn import finished. No new roles matched your filters."
  }
  if (status === "session_invalid") {
    return humanizeErrorMessage(
      data.message,
      "Your LinkedIn session expired. Reconnect in Automation below."
    )
  }
  return humanizeErrorMessage(data.message, "LinkedIn import didn't complete. Please try again.")
}
