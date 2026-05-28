/** Standalone public SPA routes (no auth shell, not rewritten to /). */

export const PRIVACY_POLICY_PATH = "/privacy-policy"

export function isPublicStandaloneRoute(pathname?: string): boolean {
  const path =
    pathname ??
    (typeof window !== "undefined" ? window.location.pathname : "")
  const normalized = path.replace(/\/$/, "") || "/"
  return normalized === PRIVACY_POLICY_PATH
}

/** Absolute URL for opening the privacy policy in a new tab. */
export function privacyPolicyHref(): string {
  const origin =
    typeof window !== "undefined" ? window.location.origin : ""
  return `${origin}${PRIVACY_POLICY_PATH}`
}
