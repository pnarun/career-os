const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? "" : "http://127.0.0.1:8001")

if (import.meta.env.PROD && !API_BASE_URL) {
  console.error(
    "[Career OS] VITE_API_BASE_URL is not set. Add it in Vercel → Environment Variables and redeploy."
  )
}

const ACCESS_KEY = "career_os_access_token"
const REFRESH_KEY = "career_os_refresh_token"

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
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export async function parseErrorMessage(response) {
  try {
    const data = await response.json()
    const detail = data?.detail
    if (typeof detail === "string") return detail
    if (detail?.message) return detail.message
    return data?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

async function refreshAccessToken() {
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

  if (response.status === 401 && getRefreshToken()) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`)
      response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
    }
  }

  return response
}
