import { apiFetch, parseErrorMessage } from "@/lib/apiClient"
import { getCareerInsights } from "@/services/notificationService"

async function getCareerGrowthSummary() {
  try {
    const response = await apiFetch("/career-analytics/growth")
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

async function getWeeklyInsights() {
  try {
    const response = await apiFetch("/career-analytics/weekly-insights")
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

function settle(promise, fallback) {
  return promise.then((value) => value).catch(() => fallback)
}

/**
 * Fast core dashboard payload (single lightweight API).
 */
export async function getDashboardCore() {
  const response = await apiFetch("/dashboard/summary")
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  const data = await response.json()
  return {
    scan: data.scan,
    applicationAnalytics: data.application_analytics,
    feed: {
      totalJobs: data.feed?.total_jobs ?? 0,
      highMatches: data.feed?.high_matches ?? 0,
      easyApply: data.feed?.easy_apply ?? 0,
      scanId: data.feed?.scan_id ?? "",
      scanTimestamp: data.feed?.scan_timestamp ?? "",
      topJobs: data.feed?.top_jobs ?? [],
    },
    unreadCount: data.unread_count ?? 0,
    automation: data.automation,
    recentApplications: data.recent_applications ?? [],
    scanStatus: data.scan_status ?? "Idle",
    growth: null,
    weekly: null,
    insights: [],
  }
}

/**
 * Lazy-loaded analytics sections (not fetched on initial mount).
 */
export async function getDashboardInsights() {
  const [growth, weekly, insights] = await Promise.all([
    settle(getCareerGrowthSummary(), null),
    settle(getWeeklyInsights(), null),
    settle(getCareerInsights(3), []),
  ])
  return { growth, weekly, insights }
}

/** @deprecated Use getDashboardCore + getDashboardInsights for progressive load */
export async function getDashboardSummary() {
  const core = await getDashboardCore()
  const extra = await getDashboardInsights()
  return { ...core, ...extra }
}

export const QUICK_LINKS = [
  {
    id: "jobs-hub",
    label: "Jobs",
    description: "Browse and filter your latest scan matches",
    accent: "text-sky-400",
  },
  {
    id: "career-hub",
    label: "Career Track",
    description: "Applications CRM and interview preparation",
    accent: "text-indigo-400",
  },
  {
    id: "insights-hub",
    label: "Intelligence",
    description: "Analytics, salary insights, and Career Copilot",
    accent: "text-teal-400",
  },
  {
    id: "resume-hub",
    label: "Resume",
    description: "Upload resume and run ATS scoring",
    accent: "text-amber-400",
  },
  {
    id: "operations-hub",
    label: "Scans & Automation",
    description: "Scheduled scans, sessions, and notifications",
    accent: "text-emerald-400",
  },
  {
    id: "settings",
    label: "Settings",
    description: "Scan schedule, email preferences, and thresholds",
    accent: "text-muted-foreground",
  },
]
