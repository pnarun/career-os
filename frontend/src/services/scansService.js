import { getAutomationAnalytics } from "@/services/notificationService"
import {
  getEmailPreview,
  getPreferences,
  runScanNow,
  sendEmailNow,
  updatePreferences,
} from "@/services/preferencesService"
import { getLatestScanAnalytics } from "@/services/scanAnalyticsService"
import { getSessionStatus } from "@/services/automationService"
import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

export const ALL_PROVIDERS = [
  { id: "linkedin", label: "LinkedIn" },
  { id: "indeed", label: "Indeed" },
  { id: "naukri", label: "Naukri" },
  { id: "instahyre", label: "Instahyre" },
  { id: "remoteok", label: "RemoteOK" },
  { id: "arbeitnow", label: "Arbeitnow" },
]

export async function getRecentScanSessions(limit = 25) {
  const response = await apiFetch(`/scan-analytics/recent?limit=${limit}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getScanSessionDetail(scanId) {
  const response = await apiFetch(`/scan-analytics/session/${encodeURIComponent(scanId)}`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function loadScanCenterData() {
  const [preferences, sessions, analytics, latestScan, browserSessions] = await Promise.all([
    getPreferences().catch(() => null),
    getRecentScanSessions(25).catch(() => []),
    getAutomationAnalytics(15).catch(() => null),
    getLatestScanAnalytics().catch(() => null),
    getSessionStatus().catch(() => ({ platforms: {} })),
  ])

  const history = buildScanHistory(sessions, analytics?.recent_runs || [], preferences)
  const diagnostics = buildProviderDiagnostics(latestScan, browserSessions, analytics)
  const stats = buildScanStats(sessions, analytics, preferences)

  return {
    preferences,
    history,
    diagnostics,
    stats,
    analytics,
    latestScan,
  }
}

function buildScanHistory(sessions, runs, preferences) {
  const rows = []
  let sessionIndex = 0
  let runIndex = 0

  for (const session of sessions) {
    const providers = Object.keys(session.sources || session.source_breakdown || {}).filter(
      (k) => (session.sources || session.source_breakdown || {})[k] > 0
    )
    const failed = session.failed_sources || []
    const status = failed.length && session.qualified_jobs > 0
      ? "Partial"
      : failed.length
        ? "Failed"
        : "Success"

    const sessionKey =
      session.scan_id ||
      session.id ||
      session.scan_timestamp ||
      session.created_at ||
      `idx-${sessionIndex}`
    sessionIndex += 1
    rows.push({
      id: `session:${sessionKey}:${session.created_at || session.scan_timestamp || sessionIndex}`,
      scanId: session.scan_id,
      started: session.scan_timestamp || session.created_at,
      duration: "—",
      providers: providers.join(", ") || `${session.platforms_scanned || 0} platforms`,
      jobsFetched: session.total_fetched ?? 0,
      qualifiedJobs: session.qualified_jobs ?? 0,
      failedProviders: failed.join(", ") || "—",
      emailSent:
        preferences?.last_email_scan_id === session.scan_id ? "Yes" : "—",
      status,
      raw: session,
      type: "scan_session",
    })
  }

  for (const run of runs) {
    if (run.run_type !== "daily_scan") continue
    const statusMap = {
      completed: "Success",
      partial: "Partial",
      failed: "Failed",
      running: "Running",
    }
    const runKey = run.id || run.scan_id || run.started_at || `idx-${runIndex}`
    runIndex += 1
    rows.push({
      id: `run:${runKey}:${run.started_at || runIndex}`,
      scanId: run.scan_id || run.id,
      started: run.started_at,
      duration: run.completed_at ? "completed" : "—",
      providers: [...(run.providers_succeeded || []), ...(run.providers_failed || [])].join(", ") || "—",
      jobsFetched: run.jobs_analyzed ?? 0,
      qualifiedJobs: run.high_matches_found ?? 0,
      failedProviders: (run.providers_failed || []).join(", ") || "—",
      emailSent: run.notifications_sent > 0 ? "Yes" : "—",
      status: statusMap[run.status] || run.status,
      raw: run,
      type: "automation_run",
    })
  }

  return rows.sort((a, b) => String(b.started).localeCompare(String(a.started)))
}

function buildProviderDiagnostics(latestScan, browserSessions, analytics) {
  const providerStatus = latestScan?.provider_status || []
  const perf = analytics?.provider_performance || {}
  const platforms = browserSessions?.platforms || {}

  return ALL_PROVIDERS.map(({ id, label }) => {
    const diag = providerStatus.find((p) => p.source === id)
    const browser = platforms[id]
    const successCount = perf[id] || 0

    let status = "unknown"
    let message = "No recent fetch data"
    if (diag) {
      status = diag.status === "success" ? "ok" : diag.status === "failed" ? "error" : "warn"
      message = diag.error_message || diag.message || (diag.jobs_fetched ? `${diag.jobs_fetched} jobs` : "OK")
    }
    if (browser?.status === "ready") {
      status = status === "error" ? status : "session_ready"
      message = browser.last_saved_at ? `Session saved ${browser.last_saved_at}` : message
    } else if (browser?.status === "corrupted") {
      status = "error"
      message = "Browser session corrupted — re-login in Automation"
    }

    return {
      id,
      label,
      status,
      message,
      lastSuccess: successCount > 0 ? `${successCount} recent successes` : "—",
      jobsFetched: diag?.jobs_fetched ?? 0,
    }
  })
}

function buildScanStats(sessions, analytics, preferences) {
  const totalQualified = sessions.reduce((s, x) => s + (x.qualified_jobs || 0), 0)
  const totalFetched = sessions.reduce((s, x) => s + (x.total_fetched || 0), 0)
  const successRate =
    sessions.length > 0
      ? Math.round(
          (sessions.filter((s) => !(s.failed_sources || []).length).length / sessions.length) * 100
        )
      : 0

  return {
    scansInHistory: sessions.length,
    scansCompleted: analytics?.scans_completed ?? 0,
    jobsAnalyzed: analytics?.jobs_analyzed ?? totalFetched,
    qualifiedTotal: totalQualified,
    providerSuccessRate: successRate,
    emailsSent: analytics?.notifications_sent ?? 0,
    lastEmailAt: preferences?.last_email_sent_at || "—",
    schedulerActive: preferences?.is_active ?? false,
  }
}

export {
  getPreferences,
  updatePreferences,
  runScanNow,
  sendEmailNow,
  getEmailPreview,
}
