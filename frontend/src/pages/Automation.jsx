import { useCallback, useEffect, useState } from "react"
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Globe,
  Loader2,
  Monitor,
  RefreshCw,
  Trash2,
  ExternalLink,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  deletePlatformSession,
  getBrowserHealth,
  getSessionStatus,
  openPlatformSession,
  screenshotUrl,
  signalManualSessionDone,
  testOpenUrl,
  testPlatformSession,
} from "@/services/automationService"
import { fetchLinkedInJobs } from "@/services/jobService"
import { cn } from "@/lib/utils"

const PLATFORMS = ["linkedin", "naukri", "indeed", "instahyre"]

const STATUS_STYLES = {
  ready: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
  corrupted: "border-red-500/40 bg-red-500/10 text-red-400",
  none: "border-border bg-muted/40 text-muted-foreground",
}

function SessionStatusBadge({ status }) {
  const key = status === "ready" || status === "corrupted" ? status : "none"
  const label =
    key === "ready" ? "Ready" : key === "corrupted" ? "Corrupted" : "None"

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium capitalize",
        STATUS_STYLES[key]
      )}
    >
      {key === "ready" && <CheckCircle2 className="size-3" />}
      {key === "corrupted" && <AlertTriangle className="size-3" />}
      {label}
    </span>
  )
}

function Toast({ toast, onDismiss }) {
  if (!toast) return null

  const isError = toast.type === "error"

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50 max-w-sm rounded-lg border px-4 py-3 text-sm shadow-lg",
        isError
          ? "border-destructive/50 bg-destructive/15 text-destructive"
          : "border-emerald-500/40 bg-emerald-500/10 text-emerald-100"
      )}
      role="status"
    >
      <div className="flex items-start justify-between gap-3">
        <p>{toast.message}</p>
        <button
          type="button"
          className="shrink-0 opacity-70 hover:opacity-100"
          onClick={onDismiss}
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>
    </div>
  )
}

function formatSavedAt(iso) {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

function PlatformSessionCard({
  platform,
  info,
  actionLoading,
  manualWait,
  doneLoading,
  onPrepare,
  onOpen,
  onManualDone,
  onDelete,
}) {
  const status = info?.status ?? "none"
  const canOpen = status === "ready"
  const isWaiting =
    manualWait?.platform === platform &&
    (manualWait.mode === "prepare" || manualWait.mode === "open")
  const doneLabel =
    manualWait?.mode === "open" ? "Done viewing session" : "Done logging in"

  return (
    <li className="rounded-lg border border-border/60 bg-background/40 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold capitalize">{platform}</span>
            <SessionStatusBadge status={status} />
          </div>
          <dl className="mt-3 grid gap-1.5 text-xs text-muted-foreground sm:grid-cols-3">
            <div>
              <dt className="uppercase tracking-wide">Last saved</dt>
              <dd className="mt-0.5 font-medium text-foreground">
                {formatSavedAt(info?.last_saved_at)}
              </dd>
            </div>
            <div>
              <dt className="uppercase tracking-wide">Cookies</dt>
              <dd className="mt-0.5 font-medium tabular-nums text-foreground">
                {info?.cookie_count ?? 0}
              </dd>
            </div>
            <div>
              <dt className="uppercase tracking-wide">Size</dt>
              <dd className="mt-0.5 font-medium tabular-nums text-foreground">
                {info?.storage_size_kb ?? 0} KB
              </dd>
            </div>
          </dl>
        </div>
        <div className="flex flex-wrap gap-2">
          {isWaiting ? (
            <Button
              type="button"
              size="sm"
              className="min-h-10 touch-manipulation"
              disabled={doneLoading}
              onClick={() => onManualDone(platform, manualWait.mode)}
            >
              {doneLoading ? (
                <Loader2 className="mr-1 size-3 animate-spin" />
              ) : (
                <CheckCircle2 className="mr-1 size-3" />
              )}
              {doneLabel}
            </Button>
          ) : (
            <>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="min-h-10 touch-manipulation"
                disabled={actionLoading === `${platform}-prepare`}
                onClick={() => onPrepare(platform)}
              >
                {actionLoading === `${platform}-prepare` && (
                  <Loader2 className="mr-1 size-3 animate-spin" />
                )}
                Prepare session
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={!canOpen || actionLoading === `${platform}-open`}
                title={
                  canOpen
                    ? "Open headed browser with saved session"
                    : "Prepare a valid session first"
                }
                onClick={() => onOpen(platform)}
              >
                {actionLoading === `${platform}-open` ? (
                  <Loader2 className="mr-1 size-3 animate-spin" />
                ) : (
                  <ExternalLink className="mr-1 size-3" />
                )}
                Open session
              </Button>
            </>
          )}
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="text-destructive hover:text-destructive"
            disabled={actionLoading === `${platform}-delete`}
            onClick={() => onDelete(platform)}
          >
            {actionLoading === `${platform}-delete` ? (
              <Loader2 className="mr-1 size-3 animate-spin" />
            ) : (
              <Trash2 className="mr-1 size-3" />
            )}
            Delete
          </Button>
        </div>
      </div>
    </li>
  )
}

export function Automation() {
  const [health, setHealth] = useState(null)
  const [sessions, setSessions] = useState({})
  const [loadingHealth, setLoadingHealth] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [testUrl, setTestUrl] = useState("https://example.com")
  const [testResult, setTestResult] = useState(null)
  const [testLoading, setTestLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState("")
  /** @type {[{ platform: string, mode: 'prepare' | 'open' } | null]} */
  const [manualWait, setManualWait] = useState(null)
  const [doneLoading, setDoneLoading] = useState(false)
  const [linkedinLoading, setLinkedinLoading] = useState(false)
  const [linkedinResult, setLinkedinResult] = useState(null)
  const [toast, setToast] = useState(null)

  const showToast = useCallback((message, type = "success") => {
    setToast({ message, type })
    window.setTimeout(() => setToast(null), 5000)
  }, [])

  const loadSessions = useCallback(async () => {
    setLoadingSessions(true)
    try {
      const data = await getSessionStatus()
      setSessions(data.sessions || {})
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to load sessions",
        "error"
      )
    } finally {
      setLoadingSessions(false)
    }
  }, [showToast])

  const runHealthCheck = useCallback(async () => {
    setLoadingHealth(true)
    try {
      const data = await getBrowserHealth()
      setHealth(data)
      showToast(data.status === "ok" ? "Browser health check passed." : data.message)
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Health check failed", "error")
      setHealth(null)
    } finally {
      setLoadingHealth(false)
    }
  }, [showToast])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  async function handleTestOpen() {
    setTestLoading(true)
    setTestResult(null)
    try {
      const data = await testOpenUrl({ url: testUrl, platform: "generic" })
      setTestResult(data)
      showToast("Screenshot captured.")
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Test open failed", "error")
    } finally {
      setTestLoading(false)
    }
  }

  async function handleManualDone(platform, mode) {
    setDoneLoading(true)
    try {
      const data = await signalManualSessionDone(platform, mode)
      showToast(data.message || "Finish signal sent…")
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Could not send done signal",
        "error"
      )
    } finally {
      setDoneLoading(false)
    }
  }

  async function handlePrepare(platform) {
    setActionLoading(`${platform}-prepare`)
    setManualWait({ platform, mode: "prepare" })
    showToast(
      `Browser opening for ${platform}. Log in on your machine, then tap Done logging in.`
    )
    try {
      await testPlatformSession(platform)
      await loadSessions()
      showToast(`Session prepare started for ${platform}. Tap Done when login is complete.`)
    } catch (err) {
      setManualWait(null)
      showToast(
        err instanceof Error ? err.message : "Prepare session failed",
        "error"
      )
    } finally {
      setActionLoading("")
    }
  }

  async function handleOpen(platform) {
    setActionLoading(`${platform}-open`)
    setManualWait({ platform, mode: "open" })
    showToast(
      `Opening ${platform} with saved session. Tap Done when finished.`
    )
    try {
      const data = await openPlatformSession(platform)
      setManualWait(null)
      showToast(data.message || "Browser closed.")
    } catch (err) {
      setManualWait(null)
      showToast(
        err instanceof Error ? err.message : "Open session failed",
        "error"
      )
    } finally {
      setActionLoading("")
    }
  }

  async function handleLinkedInDiscovery() {
    setLinkedinLoading(true)
    setLinkedinResult(null)
    try {
      const data = await fetchLinkedInJobs()
      setLinkedinResult(data)
      if (data.status === "ok" || data.status === "empty") {
        showToast(
          data.jobs_stored > 0
            ? `Stored ${data.jobs_stored} LinkedIn jobs. View them on the Jobs page.`
            : data.message || "LinkedIn fetch finished."
        )
      } else if (data.status === "session_invalid") {
        showToast(data.message || "LinkedIn session invalid.", "error")
      } else {
        showToast(data.message || "LinkedIn fetch failed.", "error")
      }
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "LinkedIn fetch failed",
        "error"
      )
    } finally {
      setLinkedinLoading(false)
    }
  }

  async function handleDelete(platform) {
    const confirmed = window.confirm(
      `Delete the saved ${platform} session? This cannot be undone.`
    )
    if (!confirmed) return

    setActionLoading(`${platform}-delete`)
    try {
      await deletePlatformSession(platform)
      await loadSessions()
      showToast(`${platform} session deleted.`)
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Delete session failed",
        "error"
      )
    } finally {
      setActionLoading("")
    }
  }

  const previewSrc = testResult?.screenshot_path
    ? screenshotUrl(testResult.screenshot_path)
    : ""

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Session control center
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Create, validate, reopen, and delete Playwright storage sessions per platform.
          No auto-apply or login automation.
        </p>
      </div>

      <section className="rounded-xl border border-border/80 bg-card/50 p-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Monitor className="size-5 text-indigo-400" />
            <h2 className="font-medium text-foreground">Browser health</h2>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={loadingHealth}
            onClick={runHealthCheck}
          >
            {loadingHealth ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 size-4" />
            )}
            Run check
          </Button>
        </div>
        {health && (
          <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-medium capitalize">{health.status}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Chromium</dt>
              <dd className="font-medium">{health.chromium_version || "—"}</dd>
            </div>
          </dl>
        )}
      </section>

      <section className="rounded-xl border border-border/80 bg-card/50 p-5">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="font-medium text-foreground">Platform sessions</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Prepare and Open keep Chromium open until you click{" "}
              <strong className="text-foreground">Done</strong> on the platform card (
              <code className="text-[11px]">PLAYWRIGHT_HEADLESS=false</code> recommended).
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={loadingSessions}
            onClick={loadSessions}
          >
            {loadingSessions ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
          </Button>
        </div>
        {manualWait && (
          <div className="mt-4 rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-3 text-sm text-indigo-100">
            <p>
              <span className="font-medium capitalize">{manualWait.platform}</span>{" "}
              is open in Chromium (
              {manualWait.mode === "open" ? "viewing session" : "prepare login"}).
              When finished, click{" "}
              <strong>
                {manualWait.mode === "open"
                  ? "Done viewing session"
                  : "Done logging in"}
              </strong>{" "}
              on that card.
            </p>
          </div>
        )}
        <ul className="mt-4 space-y-3">
          {PLATFORMS.map((platform) => (
            <PlatformSessionCard
              key={platform}
              platform={platform}
              info={sessions[platform]}
              actionLoading={actionLoading}
              manualWait={manualWait}
              doneLoading={doneLoading}
              onPrepare={handlePrepare}
              onManualDone={handleManualDone}
              onOpen={handleOpen}
              onDelete={handleDelete}
            />
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-border/80 bg-card/50 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <Briefcase className="size-5 text-indigo-400" />
            <div>
              <h2 className="font-medium text-foreground">Fetch LinkedIn Jobs</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                LinkedIn-only shortcut. Use <strong className="text-foreground">Fetch Jobs</strong> on
                the Jobs page to run all platforms (including LinkedIn) in one scan.
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={linkedinLoading}
            onClick={handleLinkedInDiscovery}
          >
            {linkedinLoading ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <Briefcase className="mr-2 size-4" />
            )}
            Fetch LinkedIn Jobs
          </Button>
        </div>
        {linkedinResult && (
          <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-medium capitalize">{linkedinResult.status}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Session valid</dt>
              <dd className="font-medium">
                {linkedinResult.session_valid ? "Yes" : "No"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Jobs fetched</dt>
              <dd className="font-medium tabular-nums">
                {linkedinResult.jobs_fetched ?? 0}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Jobs stored</dt>
              <dd className="font-medium tabular-nums">
                {linkedinResult.jobs_stored ?? 0}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Easy Apply</dt>
              <dd className="font-medium tabular-nums">
                {linkedinResult.easy_apply_count ?? 0}
              </dd>
            </div>
            {linkedinResult.search_keywords?.length > 0 && (
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">Search keywords</dt>
                <dd className="font-medium">
                  {linkedinResult.search_keywords.join(" · ")}
                </dd>
              </div>
            )}
            {linkedinResult.message && (
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">Message</dt>
                <dd>{linkedinResult.message}</dd>
              </div>
            )}
          </dl>
        )}
      </section>

      <section className="rounded-xl border border-border/80 bg-card/50 p-5">
        <div className="flex items-center gap-2">
          <Globe className="size-5 text-indigo-400" />
          <h2 className="font-medium text-foreground">Test URL open</h2>
        </div>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="url"
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm"
            placeholder="https://example.com"
          />
          <Button type="button" disabled={testLoading} onClick={handleTestOpen}>
            {testLoading && <Loader2 className="mr-2 size-4 animate-spin" />}
            Open &amp; screenshot
          </Button>
        </div>
        {testResult && (
          <div className="mt-4 space-y-3 text-sm">
            <p>
              <span className="text-muted-foreground">Title:</span>{" "}
              {testResult.title || "—"}
            </p>
            {previewSrc && (
              <img
                src={previewSrc}
                alt="Test screenshot"
                className="max-h-80 w-full rounded-lg border border-border object-contain bg-background"
              />
            )}
          </div>
        )}
      </section>

      <Toast toast={toast} onDismiss={() => setToast(null)} />
    </div>
  )
}
