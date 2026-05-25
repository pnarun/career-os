const DISMISS_KEY_PREFIX = "career_os_tour_dismissed_"
const SESSION_CLOSED_KEY = "career_os_tour_closed_session"
const SESSION_PENDING_KEY = "career_os_tour_pending_login"

export function isTourPermanentlyDismissed(userId) {
  if (!userId) return false
  try {
    return localStorage.getItem(`${DISMISS_KEY_PREFIX}${userId}`) === "1"
  } catch {
    return false
  }
}

export function permanentlyDismissTour(userId) {
  if (!userId) return
  try {
    localStorage.setItem(`${DISMISS_KEY_PREFIX}${userId}`, "1")
    sessionStorage.removeItem(SESSION_PENDING_KEY)
  } catch {
    /* ignore */
  }
}

export function isTourClosedThisSession() {
  try {
    return sessionStorage.getItem(SESSION_CLOSED_KEY) === "1"
  } catch {
    return false
  }
}

export function markTourClosedThisSession() {
  try {
    sessionStorage.setItem(SESSION_CLOSED_KEY, "1")
    sessionStorage.removeItem(SESSION_PENDING_KEY)
  } catch {
    /* ignore */
  }
}

export function markTourPendingForLogin() {
  try {
    sessionStorage.removeItem(SESSION_CLOSED_KEY)
    sessionStorage.setItem(SESSION_PENDING_KEY, "1")
  } catch {
    /* ignore */
  }
}

export function clearTourSessionForNewLogin() {
  markTourPendingForLogin()
}

export function shouldShowPlatformTour(userId) {
  if (!userId) return false
  if (isTourPermanentlyDismissed(userId)) return false
  if (isTourClosedThisSession()) return false
  try {
    if (sessionStorage.getItem(SESSION_PENDING_KEY) !== "1") return false
  } catch {
    return false
  }
  return true
}
