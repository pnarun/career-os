const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? "" : "http://127.0.0.1:8001")

if (import.meta.env.PROD && !API_BASE_URL) {
  console.error(
    "[Career OS] VITE_API_BASE_URL is not set. Add it in Vercel → Environment Variables and redeploy."
  )
}

import { humanizeErrorMessage } from "@/lib/userFacingErrors"

const ACCESS_KEY = "career_os_access_token"
const REFRESH_KEY = "career_os_refresh_token"
const REFRESH_RETRY_COOLDOWN_MS = 10_000

export const AUTH_SESSION_EXPIRED_EVENT = "career-os:session-expired"

let refreshInFlight = null
let lastRefreshFailureAt = 0

function notifySessionExpired() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(AUTH_SESSION_EXPIRED_EVENT))
  }
}

export function getApiBaseUrl() {
  return API_BASE_URL
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY) ?? ""
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY) ?? ""
}

export function setTokens({ accessToken, refreshToken }) {
  if (accessToken) localStorage.setItem(ACCESS_KEY, accessToken)
  if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken)
  lastRefreshFailureAt = 0
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export async function parseErrorMessage(response) {
  try {
    const data = await response.json()
    const detail = data?.detail
    let raw
    if (typeof detail === "string") raw = detail
    else if (detail?.message) raw = detail.message
    else raw = data?.message ?? `Request failed (${response.status})`
    return humanizeErrorMessage(raw)
  } catch {
    return humanizeErrorMessage(`Request failed (${response.status})`)
  }
}

/** Refresh tokens using the stored refresh token (used by apiFetch and realtime WS). */
export async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) return null

  const data = await response.json()
  setTokens({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
  })
  return data.access_token
}

async function refreshAccessTokenSingleFlight() {
  if (refreshInFlight) return refreshInFlight
  if (Date.now() - lastRefreshFailureAt < REFRESH_RETRY_COOLDOWN_MS) {
    return null
  }

  refreshInFlight = (async () => {
    const token = await refreshAccessToken()
    if (!token) {
      lastRefreshFailureAt = Date.now()
      clearTokens()
      return null
    }
    lastRefreshFailureAt = 0
    return token
  })()

  try {
    return await refreshInFlight
  } finally {
    refreshInFlight = null
  }
}

/**
 * Authenticated fetch with automatic token refresh on 401.
 */
export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }

  const token = getAccessToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)

  let response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (response.status === 401) {
    if (getRefreshToken()) {
      const newToken = await refreshAccessTokenSingleFlight()
      if (newToken) {
        headers.set("Authorization", `Bearer ${newToken}`)
        response = await fetch(`${API_BASE_URL}${path}`, {
          ...options,
          headers,
          signal: options.signal,
        })
      }
    }
    if (response.status === 401) {
      notifySessionExpired()
    }
  }

  return response
}
