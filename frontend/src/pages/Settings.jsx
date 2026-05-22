import { useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  Loader2,
  Mail,
  Play,
  Radar,
  Save,
} from "lucide-react"

import { EmailPreviewModal } from "@/components/EmailPreviewModal"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  getEmailPreview,
  getPreferences,
  listResumes,
  runScanNow,
  savePreferences,
  sendEmailNow,
  updatePreferences,
} from "@/services/preferencesService"

const FREQUENCY_OPTIONS = [{ value: "daily", label: "Daily" }]

const TIMEZONE_OPTIONS = [
  "Asia/Kolkata",
  "Asia/Dubai",
  "Europe/Berlin",
  "Europe/London",
  "America/New_York",
  "UTC",
]

const defaultForm = {
  email: "",
  resume_id: "",
  scan_time: "08:00",
  timezone: "Asia/Kolkata",
  frequency: "daily",
  is_active: true,
}

export function Settings() {
  const [form, setForm] = useState(defaultForm)
  const [preferenceId, setPreferenceId] = useState(null)
  const [resumes, setResumes] = useState([])
  const [status, setStatus] = useState("idle")
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  const [scanSummary, setScanSummary] = useState(null)
  const [emailDelivery, setEmailDelivery] = useState(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewHtml, setPreviewHtml] = useState("")
  const [previewMeta, setPreviewMeta] = useState({})
  const [previewLoading, setPreviewLoading] = useState(false)

  const loadData = useCallback(async () => {
    setStatus("loading")
    setError(null)
    try {
      const [prefs, resumeList] = await Promise.all([
        getPreferences(),
        listResumes(),
      ])
      setResumes(resumeList)

      if (prefs) {
        setPreferenceId(prefs.id)
        setForm({
          email: prefs.email ?? "",
          resume_id: prefs.resume_id ?? "",
          scan_time: prefs.scan_time ?? "08:00",
          timezone: prefs.timezone ?? "Asia/Kolkata",
          frequency: prefs.frequency ?? "daily",
          is_active: prefs.is_active ?? true,
        })
      } else if (resumeList.length > 0) {
        setForm((prev) => ({
          ...prev,
          resume_id: resumeList[0].id,
          email: resumeList[0].emails?.[0] ?? prev.email,
        }))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings")
    } finally {
      setStatus("idle")
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const onChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setMessage(null)
    setError(null)
  }

  const onSave = async () => {
    setStatus("saving")
    setError(null)
    setMessage(null)

    try {
      if (!form.email.trim()) {
        throw new Error("Email address is required")
      }
      if (!form.resume_id) {
        throw new Error("Select a resume for matching")
      }

      const payload = {
        email: form.email.trim(),
        resume_id: form.resume_id,
        scan_time: form.scan_time,
        timezone: form.timezone,
        frequency: form.frequency,
        is_active: form.is_active,
      }

      if (preferenceId) {
        const updated = await updatePreferences(preferenceId, payload)
        setPreferenceId(updated.id)
        setMessage("Preferences updated. Scheduled scan synced.")
      } else {
        const saved = await savePreferences(payload)
        setPreferenceId(saved.id)
        setMessage("Preferences saved. Daily scan scheduled.")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save preferences")
    } finally {
      setStatus("idle")
    }
  }

  const onRunScanNow = async () => {
    if (!preferenceId) {
      setError("Save preferences first before running a scan.")
      return
    }

    setStatus("scanning")
    setError(null)
    setMessage(null)
    setScanSummary(null)

    try {
      const result = await runScanNow(preferenceId)
      setScanSummary(result)

      if (result.email_sent) {
        setEmailDelivery({
          sent: true,
          jobs_sent: result.jobs_found ?? 0,
          email_to: result.email_to,
          sent_at: result.scan_timestamp,
          email_type: (result.jobs_found ?? 0) > 0 ? "opportunities" : "no_match",
        })
        setMessage(
          (result.jobs_found ?? 0) > 0
            ? `Scan complete — ${result.jobs_found} jobs emailed to ${result.email_to}.`
            : `Scan complete — daily update emailed to ${result.email_to} (no strong matches).`
        )
      } else if (result.email_error) {
        setMessage(
          `Scan complete (stored ${result.stored ?? 0}) but email not sent: ${result.email_error}`
        )
      } else {
        setMessage(`Scan complete — ${result.jobs_found} jobs in digest.`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Manual scan failed")
    } finally {
      setStatus("idle")
    }
  }

  const onPreviewEmail = async () => {
    setPreviewOpen(true)
    setPreviewLoading(true)
    setPreviewHtml("")
    setError(null)

    try {
      const result = await getEmailPreview(form.resume_id || undefined)
      setPreviewHtml(result.preview_html)
      setPreviewMeta({
        jobsCount: result.jobs_count,
        scanId: result.scan_id,
        scanTimestamp: result.scan_timestamp,
      })
    } catch (err) {
      setPreviewOpen(false)
      setError(err instanceof Error ? err.message : "Failed to load email preview")
    } finally {
      setPreviewLoading(false)
    }
  }

  const isSaving = status === "saving"
  const isLoading = status === "loading"
  const onSendEmail = async () => {
    if (!preferenceId) {
      setError("Save preferences first before sending email.")
      return
    }

    setStatus("sending_email")
    setError(null)
    setMessage(null)

    try {
      const result = await sendEmailNow(preferenceId)
      setEmailDelivery(result)

      if (result.email_sent) {
        const label =
          result.email_type === "no_match"
            ? "Daily scan complete email"
            : `${result.jobs_sent} opportunities`
        setMessage(`${label} sent to ${result.email_to}.`)
      } else {
        setError(result.error || "Email was not sent.")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send email")
    } finally {
      setStatus("idle")
    }
  }

  const isScanning = status === "scanning"
  const isSendingEmail = status === "sending_email"

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Settings</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Your AI career automation control center — schedule scans, test delivery, and preview emails.
        </p>
      </div>

      <Card className="border-indigo-500/20 bg-indigo-500/5">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Radar className="size-5 text-indigo-400" />
            <CardTitle className="text-base">Automation testing</CardTitle>
          </div>
          <CardDescription>
            Run an instant scan and send a real curated email, or preview formatting before delivery.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={onRunScanNow}
              disabled={isScanning || isLoading || !preferenceId}
            >
              {isScanning ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Running scan…
                </>
              ) : (
                <>
                  <Play className="size-4" />
                  Run Scan Now
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={onSendEmail}
              disabled={isSendingEmail || isLoading || !preferenceId}
            >
              {isSendingEmail ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Sending…
                </>
              ) : (
                <>
                  <Mail className="size-4" />
                  Send Email
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={onPreviewEmail}
              disabled={previewLoading || isLoading}
            >
              {previewLoading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Loading…
                </>
              ) : (
                <>
                  <Eye className="size-4" />
                  Preview Email
                </>
              )}
            </Button>
          </div>

          {emailDelivery && (
            <div className="rounded-lg border border-border bg-background/60 px-3 py-3 text-sm">
              <p className="font-medium text-foreground">Last email delivery</p>
              <ul className="mt-2 space-y-1 text-muted-foreground">
                <li>
                  Sent:{" "}
                  <span
                    className={
                      emailDelivery.email_sent !== false
                        ? "text-green-400"
                        : "text-amber-400"
                    }
                  >
                    {emailDelivery.email_sent !== false ? "Yes" : "No"}
                  </span>
                </li>
                <li>
                  To:{" "}
                  <span className="text-foreground">
                    {emailDelivery.email_to || form.email}
                  </span>
                </li>
                <li>
                  Jobs included:{" "}
                  <span className="text-foreground">
                    {emailDelivery.jobs_sent ?? 0}
                  </span>
                  {emailDelivery.email_type === "no_match" && (
                    <span className="text-xs text-muted-foreground">
                      {" "}
                      (no-match digest)
                    </span>
                  )}
                </li>
                {emailDelivery.sent_at && (
                  <li>
                    Timestamp:{" "}
                    <span className="text-foreground">{emailDelivery.sent_at}</span>
                  </li>
                )}
              </ul>
            </div>
          )}

          {!preferenceId && (
            <p className="text-xs text-amber-400">
              Save preferences below to enable manual scan and email delivery.
            </p>
          )}

          {scanSummary && (
            <div className="rounded-lg border border-border bg-background/60 px-3 py-3 text-sm">
              <p className="font-medium text-foreground">Last manual scan</p>
              <ul className="mt-2 space-y-1 text-muted-foreground">
                <li>
                  Status: <span className="text-foreground">{scanSummary.status}</span>
                </li>
                <li>
                  Scan ID:{" "}
                  <span className="font-mono text-xs text-foreground">
                    {scanSummary.scan_id}
                  </span>
                </li>
                <li>
                  Jobs in email:{" "}
                  <span className="text-foreground">{scanSummary.jobs_found}</span>
                </li>
                <li>
                  Stored in batch:{" "}
                  <span className="text-foreground">{scanSummary.stored ?? "—"}</span>
                </li>
                <li>
                  Email sent:{" "}
                  <span
                    className={
                      scanSummary.email_sent ? "text-green-400" : "text-amber-400"
                    }
                  >
                    {scanSummary.email_sent ? `Yes → ${scanSummary.email_to}` : "No"}
                  </span>
                </li>
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Scan preferences</CardTitle>
          <CardDescription>
            Career OS runs an intelligent scan daily and emails your top matches automatically.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading preferences…
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <label htmlFor="email" className="text-sm font-medium">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(e) => onChange("email", e.target.value)}
                  placeholder="you@example.com"
                  className="flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="resume" className="text-sm font-medium">
                  Resume for matching
                </label>
                <select
                  id="resume"
                  value={form.resume_id}
                  onChange={(e) => onChange("resume_id", e.target.value)}
                  disabled={resumes.length === 0}
                  className="flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
                >
                  <option value="">
                    {resumes.length === 0
                      ? "Upload a resume first"
                      : "Select resume"}
                  </option>
                  {resumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.filename || resume.id}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label htmlFor="scan_time" className="text-sm font-medium">
                    Scan delivery time
                  </label>
                  <input
                    id="scan_time"
                    type="time"
                    value={form.scan_time}
                    onChange={(e) => onChange("scan_time", e.target.value)}
                    className="flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
                  />
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="timezone" className="text-sm font-medium">
                    Timezone
                  </label>
                  <select
                    id="timezone"
                    value={form.timezone}
                    onChange={(e) => onChange("timezone", e.target.value)}
                    className="flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
                  >
                    {TIMEZONE_OPTIONS.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="frequency" className="text-sm font-medium">
                  Frequency
                </label>
                <select
                  id="frequency"
                  value={form.frequency}
                  onChange={(e) => onChange("frequency", e.target.value)}
                  className="flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
                >
                  {FREQUENCY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => onChange("is_active", e.target.checked)}
                  className="size-4 rounded border-border"
                />
                <span>Active — enable scheduled scans and emails</span>
              </label>
            </>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="flex items-start gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-400">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
              <span>{message}</span>
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button onClick={onSave} disabled={isSaving || isLoading}>
              {isSaving ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Saving…
                </>
              ) : (
                <>
                  <Save className="size-4" />
                  {preferenceId ? "Update Preferences" : "Save Preferences"}
                </>
              )}
            </Button>
          </div>

          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Mail className="size-3.5" />
            Emails include up to 15 top matched jobs with apply links (Resend).
          </p>
        </CardContent>
      </Card>

      <EmailPreviewModal
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        previewHtml={previewHtml}
        loading={previewLoading}
        meta={previewMeta}
      />
    </div>
  )
}
