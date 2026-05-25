import { getApplicationAnalytics, getApplications } from "@/services/applicationService"
import { getJobsFeed } from "@/services/jobFeedService"
import {
  getAutomationAnalytics,
  getCareerInsights,
  getUnreadCount,
} from "@/services/notificationService"
import { getLatestScanAnalytics } from "@/services/scanAnalyticsService"
import { apiFetch } from "@/lib/apiClient"

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
 * Aggregate live data for the home dashboard.
 */
export async function getDashboardSummary() {
  const [
    scan,
    applicationAnalytics,
    feed,
    unread,
    automation,
    growth,
    weekly,
    applications,
    insights,
  ] = await Promise.all([
    settle(getLatestScanAnalytics(), null),
    settle(getApplicationAnalytics(), null),
    settle(getJobsFeed(), { jobs: [], total_jobs: 0 }),
    settle(getUnreadCount(), { unread_count: 0 }),
    settle(getAutomationAnalytics(5), null),
    settle(getCareerGrowthSummary(), null),
    settle(getWeeklyInsights(), null),
    settle(getApplications(), []),
    settle(getCareerInsights(3), []),
  ])

  const jobs = feed.jobs ?? []
  const totalJobs = feed.total_jobs ?? jobs.length
  const highMatches = jobs.filter((j) => (j.match_percentage ?? 0) >= 75).length
  const easyApply = jobs.filter((j) => j.easy_apply).length
  const topJobs = [...jobs]
    .sort((a, b) => (b.match_percentage ?? 0) - (a.match_percentage ?? 0))
    .slice(0, 5)

  const recentApplications = [...applications]
    .sort((a, b) => String(b.updated_at || b.applied_at || "").localeCompare(String(a.updated_at || a.applied_at || "")))
    .slice(0, 5)

  const scanStatus = automation?.recent_runs?.length
    ? automation.recent_runs[0].status ?? "Active"
    : scan?.qualified_jobs
      ? "Ready"
      : "Idle"

  return {
    scan,
    applicationAnalytics,
    feed: {
      totalJobs,
      highMatches,
      easyApply,
      scanId: feed.scan_id ?? scan?.scan_id ?? "",
      scanTimestamp: feed.scan_timestamp ?? scan?.scan_timestamp ?? "",
      topJobs,
    },
    unreadCount: unread.unread_count ?? 0,
    automation,
    growth,
    weekly,
    recentApplications,
    insights,
    scanStatus,
  }
}

export const QUICK_LINKS = [
  {
    id: "jobs",
    label: "Jobs",
    description: "Browse and filter your latest scan matches",
    accent: "text-sky-400",
  },
  {
    id: "applications",
    label: "Applications",
    description: "Track saved jobs, applications, and interview stages",
    accent: "text-indigo-400",
  },
  {
    id: "career-analytics",
    label: "Career Analytics",
    description: "Market trends, salary insights, and growth score",
    accent: "text-teal-400",
  },
  {
    id: "interview-prep",
    label: "Interview Prep",
    description: "Mock interviews and readiness for saved roles",
    accent: "text-violet-400",
  },
  {
    id: "resume-ai",
    label: "Resume AI",
    description: "ATS scoring, keywords, and job-specific tailoring",
    accent: "text-amber-400",
  },
  {
    id: "scans",
    label: "Scans",
    description: "Run scans, scheduling, history, and email delivery",
    accent: "text-emerald-400",
  },
  {
    id: "automation",
    label: "Automation",
    description: "Browser sessions for LinkedIn and provider login",
    accent: "text-cyan-400",
  },
  {
    id: "notifications",
    label: "Notifications",
    description: "High-match alerts, digests, and career insights",
    accent: "text-rose-400",
  },
  {
    id: "career-copilot",
    label: "Career Copilot",
    description: "Ask career questions and get grounded AI guidance",
    accent: "text-indigo-400",
  },
  {
    id: "settings",
    label: "Settings",
    description: "Scan schedule, email preferences, and thresholds",
    accent: "text-muted-foreground",
  },
]
