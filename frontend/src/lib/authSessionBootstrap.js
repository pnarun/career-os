import { getAccessToken } from "@/lib/apiClient"
import * as authService from "@/services/authService"

/** Shared in-flight /auth/me so React StrictMode remount does not hang on a second cold start. */
let inflight = null
let cachedUser = null

export function clearSessionBootstrap() {
  inflight = null
  cachedUser = null
}

export function setSessionBootstrapUser(user) {
  cachedUser = user
}

export async function resolveSession() {
  const token = getAccessToken()
  if (!token) {
    cachedUser = null
    return null
  }
  if (cachedUser) {
    return cachedUser
  }
  if (!inflight) {
    inflight = authService
      .fetchMe()
      .then((me) => {
        cachedUser = me
        return me
      })
      .catch(() => {
        cachedUser = null
        return null
      })
      .finally(() => {
        inflight = null
      })
  }
  return inflight
}
