const NEW_USER_SESSION_KEY = "career_os_new_user_registration"
const RESUME_GATE_SKIPPED_PREFIX = "career_os_resume_gate_skipped_"

export function markNewUserRegistration() {
  sessionStorage.setItem(NEW_USER_SESSION_KEY, "1")
}

export function clearNewUserRegistration() {
  sessionStorage.removeItem(NEW_USER_SESSION_KEY)
}

export function isNewUserRegistration() {
  return sessionStorage.getItem(NEW_USER_SESSION_KEY) === "1"
}

export function markResumeGateSkipped(userId) {
  if (!userId) return
  localStorage.setItem(`${RESUME_GATE_SKIPPED_PREFIX}${userId}`, "1")
}

export function isResumeGateSkipped(userId) {
  if (!userId) return false
  return localStorage.getItem(`${RESUME_GATE_SKIPPED_PREFIX}${userId}`) === "1"
}

export function clearResumeGateSkipped(userId) {
  if (!userId) return
  localStorage.removeItem(`${RESUME_GATE_SKIPPED_PREFIX}${userId}`)
}
