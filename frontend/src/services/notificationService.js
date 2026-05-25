import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

export const NOTIFICATION_TYPES = {
  high_match: "High Match Alerts",
  daily_digest: "Daily Digests",
  follow_up: "Follow-up Reminders",
  interview_reminder: "Interview Reminders",
  weekly_insights: "Career Insights",
  scan_complete: "Scan Updates",
  remote_jobs: "Remote Jobs",
}

export const NOTIFICATION_TABS = [
  { id: "all", label: "All" },
  { id: "high_match", label: "High Match" },
  { id: "daily_digest", label: "Digests" },
  { id: "follow_up", label: "Follow-ups" },
  { id: "interview_reminder", label: "Interviews" },
  { id: "weekly_insights", label: "Insights" },
]

export async function getNotifications(options = {}) {
  const params = new URLSearchParams()
  if (options.unreadOnly) params.set("unread_only", "true")
  if (options.type) params.set("type", options.type)
  if (options.limit) params.set("limit", String(options.limit))

  const query = params.toString()
  const response = await apiFetch(`/notifications${query ? `?${query}` : ""}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getUnreadCount() {
  const response = await apiFetch(`/notifications/unread-count`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function markNotificationRead(notificationId) {
  const response = await apiFetch(`/notifications/${notificationId}/read`, {
    method: "PATCH",
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function markAllNotificationsRead() {
  const response = await apiFetch(`/notifications/read-all`, {
    method: "POST",
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getAutomationAnalytics(limit = 10) {
  const params = new URLSearchParams({ limit: String(limit) })
  const response = await apiFetch(`/automation/analytics?${params}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getCareerInsights(limit = 20) {
  const params = new URLSearchParams({ limit: String(limit) })
  const response = await apiFetch(`/career-insights?${params}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function generateCareerInsights() {
  const response = await apiFetch(`/career-insights/generate`, {
    method: "POST",
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}
