import { useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  Loader2,
  Mail,
  Play,
  Radar,
  RefreshCw,
  RotateCcw,
} from "lucide-react"

import { EmailPreviewModal } from "@/components/EmailPreviewModal"
import { LiveExecutionTimeline } from "@/components/scans/LiveExecutionTimeline"
import { ScanDetailModal } from "@/components/scans/ScanDetailModal"
import { useRealtime } from "@/context/RealtimeContext"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { listResumes } from "@/services/preferencesService"
import {
  ALL_PROVIDERS,
  getEmailPreview,
  getPreferences,
  loadScanCenterData,
  runScanNow,
  sendEmailNow,
  updatePreferences,
} from "@/services/scansService"

const TIMEZONE_OPTIONS = [
  "Asia/Kolkata",
  "Asia/Dubai",
  "Europe/Berlin",
  "Europe/London",
  "America/New_York",
  "UTC",
]

const STATUS_CLASS = {
  Success: "text-emerald-400",
  Partial: "text-amber-400",
  Failed: "text-red-400",
  Running: "text-sky-400",
}

function StatCell({ label, value, sub }) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/50 px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold tabular-nums">{value}</p>
      {sub ? <p className="text-[10px] text-muted-foreground">{sub}</p> : null}
    </div>
  )
}

export function Scans() {
  const { connected, feedVersion } = useRealtime()
  const [data, setData] = useState(null)
  const [prefs, setPrefs] = useState(null)
  const [preferenceId, setPreferenceId] = useState(null)
  const [resumes, setResumes] = useState([])
  const [schedule, setSchedule] = useState({
    scan_time: "08:00",
    timezone: "Asia/Kolkata",
    frequency: "daily",
    is_active: true,
    resume_id: "",
    auto_email_on_scan: true,
  })
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)
  const [selectedRow, setSelectedRow] = useState(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewHtml, setPreviewHtml] = useState("")
  const [previewMeta, setPreviewMeta] = useState({})
  const [logsOpen, setLogsOpen] = useState(false)
  const [executionLogs, setExecutionLogs] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [center, resumeList, preferences] = await Promise.all([
        loadScanCenterData(),
        listResumes(),
        getPreferences(),
      ])
      setData(center)
      setResumes(resumeList)
      if (preferences) {
        setPrefs(preferences)
        setPreferenceId(preferences.id)
        setSchedule({
          scan_time: preferences.scan_time ?? "08:00",
          timezone: preferences.timezone ?? "Asia/Kolkata",
          frequency: preferences.frequency ?? "daily",
          is_active: preferences.is_active ?? true,
          resume_id: preferences.resume_id ?? "",
          auto_email_on_scan: preferences.auto_email_on_scan ?? true,
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scan center")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (feedVersion > 0) {
      load()
    }
  }, [feedVersion, load])

  const requirePrefs = () => {
    if (!preferenceId) {
      setError("Configure email and resume in Settings first, then save preferences.")
      return false
    }
    return true
  }

  const pushLog = (text) => {
    setExecutionLogs((prev) => [
      ...prev,
      { at: new Date().toLocaleTimeString(), text },
    ])
    setLogsOpen(true)
  }

  const onRunScan = async () => {
    if (!requirePrefs()) return
    setBusy("scan")
    setError(null)
    setMessage(null)
    pushLog("Starting manual scan…")
    try {
      const result = await runScanNow(preferenceId)
      pushLog(`Scan complete — ${result.jobs_found ?? 0} jobs, stored ${result.stored ?? 0}`)
      setMessage(
        result.email_sent
          ? `Scan complete — ${result.jobs_found} jobs emailed.`
          : `Scan complete — ${result.jobs_found} jobs found.`
      )
      await load()
    } catch (err) {
      pushLog(`Scan failed: ${err.message}`)
      setError(err instanceof Error ? err.message : "Scan failed")
    } finally {
      setBusy(null)
    }
  }

  const onSendTestEmail = async () => {
    if (!requirePrefs()) return
    setBusy("email")
    setError(null)
    try {
      const result = await sendEmailNow(preferenceId)
      setMessage(result.email_sent ? `Email sent to ${result.email_to}` : result.error || "Email not sent")
      pushLog(result.email_sent ? "Test email sent" : "Email send failed")
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Email failed")
    } finally {
      setBusy(null)
    }
  }

  const onPreview = async () => {
    setPreviewOpen(true)
    setBusy("preview")
    try {
      const result = await getEmailPreview(schedule.resume_id || undefined)
      setPreviewHtml(result.preview_html)
      setPreviewMeta({
        jobsCount: result.jobs_count,
        scanId: result.scan_id,
        scanTimestamp: result.scan_timestamp,
      })
    } catch (err) {
      setPreviewOpen(false)
      setError(err instanceof Error ? err.message : "Preview failed")
    } finally {
      setBusy(null)
    }
  }

  const onSaveSchedule = async () => {
    if (!preferenceId || !prefs) {
      setError("Save user preferences in Settings first.")
      return
    }
    setBusy("schedule")
    try {
      await updatePreferences(preferenceId, {
        ...prefs,
        scan_time: schedule.scan_time,
        timezone: schedule.timezone,
        frequency: schedule.frequency,
        is_active: schedule.is_active,
        resume_id: schedule.resume_id,
        auto_email_on_scan: schedule.auto_email_on_scan,
      })
      setMessage("Scheduled automation updated.")
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save schedule")
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const stats = data?.stats || {}

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Radar className="size-6 text-indigo-400" />
            <h2 className="text-2xl font-semibold tracking-tight">Automation & Scan Center</h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Run scans, schedule automation, monitor history, and manage email delivery
            {connected ? (
              <span className="ml-2 inline-flex items-center gap-1 text-emerald-400">
                <span className="size-1.5 rounded-full bg-emerald-400" />
                Live
              </span>
            ) : null}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <RefreshCw className="mr-2 size-4" />
          Refresh
        </Button>
      </div>

      {!preferenceId && (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
          Complete Settings → User Preferences (email + resume) before running automation.
        </p>
      )}

      {error && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </p>
      )}
      {message && (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
          {message}
        </p>
      )}

      <Card className="border-indigo-500/20 bg-indigo-500/5">
        <CardContent className="flex flex-wrap gap-3 pt-6">
          <Button onClick={onRunScan} disabled={!!busy || !preferenceId}>
            {busy === "scan" ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            Run Scan Now
          </Button>
          <Button variant="outline" onClick={onSendTestEmail} disabled={!!busy || !preferenceId}>
            {busy === "email" ? <Loader2 className="size-4 animate-spin" /> : <Mail className="size-4" />}
            Send Test Email
          </Button>
          <Button variant="outline" onClick={onPreview} disabled={!!busy}>
            <Eye className="size-4" />
            Preview Digest
          </Button>
          <Button variant="outline" onClick={onRunScan} disabled={!!busy || !preferenceId}>
            <RotateCcw className="size-4" />
            Retry Failed Providers
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCell label="Scans recorded" value={stats.scansInHistory ?? 0} />
        <StatCell label="Jobs analyzed" value={stats.jobsAnalyzed ?? 0} sub={`${stats.qualifiedTotal ?? 0} qualified`} />
        <StatCell label="Provider success" value={`${stats.providerSuccessRate ?? 0}%`} />
        <StatCell
          label="Email delivery"
          value={stats.emailsSent ?? 0}
          sub={stats.schedulerActive ? "Scheduler on" : "Scheduler off"}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Scheduled Automation</CardTitle>
            <CardDescription>When and how Career OS runs scans automatically</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={schedule.is_active}
                onChange={(e) => setSchedule((s) => ({ ...s, is_active: e.target.checked }))}
              />
              Enable scheduled scans
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-xs text-muted-foreground">Frequency</label>
                <select
                  value={schedule.frequency}
                  onChange={(e) => setSchedule((s) => ({ ...s, frequency: e.target.value }))}
                  className="mt-1 flex h-9 w-full rounded-lg border border-input bg-background px-2 text-sm"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Scan time</label>
                <input
                  type="time"
                  value={schedule.scan_time}
                  onChange={(e) => setSchedule((s) => ({ ...s, scan_time: e.target.value }))}
                  className="mt-1 flex h-9 w-full rounded-lg border border-input bg-background px-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Timezone</label>
                <select
                  value={schedule.timezone}
                  onChange={(e) => setSchedule((s) => ({ ...s, timezone: e.target.value }))}
                  className="mt-1 flex h-9 w-full rounded-lg border border-input bg-background px-2 text-sm"
                >
                  {TIMEZONE_OPTIONS.map((tz) => (
                    <option key={tz} value={tz}>
                      {tz}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Resume for scan</label>
                <select
                  value={schedule.resume_id}
                  onChange={(e) => setSchedule((s) => ({ ...s, resume_id: e.target.value }))}
                  className="mt-1 flex h-9 w-full rounded-lg border border-input bg-background px-2 text-sm"
                >
                  <option value="">Select resume</option>
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.filename || r.id}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={schedule.auto_email_on_scan}
                onChange={(e) => setSchedule((s) => ({ ...s, auto_email_on_scan: e.target.checked }))}
              />
              Auto-send email after scan
            </label>
            <Button size="sm" onClick={onSaveSchedule} disabled={busy === "schedule" || !preferenceId}>
              Save schedule
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Email Delivery Center</CardTitle>
            <CardDescription>Digest delivery status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              Recipient: <span className="text-foreground">{prefs?.email || "—"}</span>
            </p>
            <p>
              Last sent: <span className="text-foreground">{stats.lastEmailAt || "Never"}</span>
            </p>
            <p>
              Digest frequency: <span className="text-foreground">{prefs?.digest_frequency || "daily"}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              Up to 15 top matched jobs per email via Resend.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-sky-500/20 bg-sky-500/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Live Automation Timeline</CardTitle>
          <CardDescription>Real-time scan and provider events as they happen</CardDescription>
        </CardHeader>
        <CardContent>
          <LiveExecutionTimeline />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Provider Diagnostics</CardTitle>
          <CardDescription>Fetch health and browser session status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {(data?.diagnostics || []).map((d) => (
              <div key={d.id} className="rounded-lg border border-border bg-muted/10 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{d.label}</span>
                  {d.status === "ok" || d.status === "session_ready" ? (
                    <CheckCircle2 className="size-4 text-emerald-400" />
                  ) : (
                    <AlertCircle className="size-4 text-amber-400" />
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{d.message}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {logsOpen && executionLogs.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Execution log</CardTitle>
          </CardHeader>
          <CardContent className="max-h-40 space-y-1 overflow-y-auto font-mono text-xs text-muted-foreground">
            {executionLogs.map((log, i) => (
              <p key={i}>
                [{log.at}] {log.text}
              </p>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Scan History</CardTitle>
          <CardDescription>Click a row for provider breakdown and errors</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[800px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="pb-2 pr-3">Scan ID</th>
                <th className="pb-2 pr-3">Started</th>
                <th className="pb-2 pr-3">Providers</th>
                <th className="pb-2 pr-3">Fetched</th>
                <th className="pb-2 pr-3">Qualified</th>
                <th className="pb-2 pr-3">Failed</th>
                <th className="pb-2 pr-3">Email</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {(data?.history || []).map((row) => (
                <tr
                  key={row.id}
                  className="cursor-pointer border-b border-border/50 hover:bg-muted/20"
                  onClick={() => setSelectedRow(row)}
                >
                  <td className="py-2 pr-3 font-mono text-xs">{row.scanId?.slice(0, 8)}…</td>
                  <td className="py-2 pr-3 text-xs">{row.started}</td>
                  <td className="max-w-[120px] truncate py-2 pr-3 text-xs">{row.providers}</td>
                  <td className="py-2 pr-3 tabular-nums">{row.jobsFetched}</td>
                  <td className="py-2 pr-3 tabular-nums">{row.qualifiedJobs}</td>
                  <td className="max-w-[100px] truncate py-2 pr-3 text-xs">{row.failedProviders}</td>
                  <td className="py-2 pr-3">{row.emailSent}</td>
                  <td className={cn("py-2 font-medium", STATUS_CLASS[row.status])}>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.history?.length && (
            <p className="py-6 text-center text-sm text-muted-foreground">No scan history yet.</p>
          )}
        </CardContent>
      </Card>

      <ScanDetailModal open={!!selectedRow} row={selectedRow} onClose={() => setSelectedRow(null)} />

      <EmailPreviewModal
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        previewHtml={previewHtml}
        loading={busy === "preview"}
        meta={previewMeta}
      />
    </div>
  )
}
