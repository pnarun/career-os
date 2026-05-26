import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"

export async function getCareerAnalyticsDashboard(role = "") {
  const params = role?.trim() ? `?role=${encodeURIComponent(role.trim())}` : ""
  const response = await apiFetch(`/career-analytics/dashboard${params}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export function scoreColor(score) {
  if (score >= 85) return "text-emerald-400"
  if (score >= 70) return "text-sky-400"
  if (score >= 50) return "text-amber-400"
  return "text-red-400"
}

export function formatSalary(value) {
  if (typeof value === "string") return value
  if (typeof value === "number") return `₹${value.toLocaleString("en-IN")}`
  return "—"
}

export const PROVIDER_COLORS = [
  "#6366f1",
  "#0ea5e9",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
]
