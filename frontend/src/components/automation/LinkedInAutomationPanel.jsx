import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Briefcase,
  CheckCircle2,
  ExternalLink,
  Puzzle,
  HelpCircle,
  Loader2,
  Monitor,
  RefreshCw,
  ShieldCheck,
  Smartphone,
  Unplug,
} from "lucide-react"

import { LinkedInOnboardingSteps } from "@/components/automation/LinkedInOnboardingSteps"
import { Button } from "@/components/ui/button"
import { useAutomationBootstrap } from "@/hooks/useAutomationBootstrap"
import {
  disconnectLinkedIn,
  generateLinkedInPairingCode,
} from "@/services/automationService"
import { humanizeErrorMessage } from "@/lib/userFacingErrors"
import { cn } from "@/lib/utils"

const LINKEDIN_RECONNECT_HINT_DAYS = 90
const CHROME_EXTENSIONS_URL = "chrome://extensions/"

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

function isMobileOrTabletViewport() {
  if (typeof window === "undefined" || !window.matchMedia) return false
  return window.matchMedia("(max-width: 1024px), (pointer: coarse)").matches
}

function normalizePairingPayload(data) {
  if (!data) return null
  const expiresIn = Number(data.expiresIn ?? data.expires_in ?? 300)
  let expiresAt = data.expiresAt ?? data.expires_at ?? null
  if (!expiresAt && expiresIn > 0) {
    expiresAt = new Date(Date.now() + expiresIn * 1000).toISOString()
  }
  const pairingCode = String(data.pairingCode ?? data.pairing_code ?? "").trim()
  if (!pairingCode) return null
  return { pairingCode, expiresIn, expiresAt }
}

function daysSinceIso(iso) {
  if (!iso) return null
  try {
    const ms = Date.now() - new Date(iso).getTime()
    if (Number.isNaN(ms) || ms < 0) return 0
    return Math.floor(ms / (1000 * 60 * 60 * 24))
  } catch {
    return null
  }
}

function TrustCallout() {
  return (
    <div className="rounded-lg border border-indigo-500/25 bg-indigo-500/5 p-4 text-sm">
      <div className="flex items-center gap-2 font-medium text-indigo-100">
        <ShieldCheck className="size-4 shrink-0 text-indigo-400" />
        Your data stays yours
      </div>
      <ul className="mt-2 space-y-1.5 text-xs leading-relaxed text-muted-foreground">
        <li>
          Career Lens only uses your LinkedIn session to fetch jobs you already have access to.
        </li>
        <li>We never collect passwords or browsing history.</li>
        <li>Setup is required only once on desktop — then automation runs in the cloud.</li>
      </ul>
    </div>
  )
}

function StatusPill({ label, value, tone = "neutral" }) {
  const toneClass =
    tone === "good"
      ? "text-emerald-400"
      : tone === "warn"
        ? "text-amber-300"
        : "text-foreground"
  return (
    <div className="rounded-lg border border-border/70 bg-background/40 p-3 text-sm">
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className={cn("mt-1 font-medium", toneClass)}>{value}</p>
    </div>
  )
}

export function LinkedInAutomationPanel({ showToast, onSessionsChange }) {
  const [isMobileSetupFlow, setIsMobileSetupFlow] = useState(false)
  const [pairingData, setPairingData] = useState(null)
  const [pairingLoading, setPairingLoading] = useState(false)
  const [pairingSecondsLeft, setPairingSecondsLeft] = useState(0)
  const {
    data: bootstrap,
    isLoading: bootstrapLoading,
    isFetching: bootstrapFetching,
    refetch: refetchBootstrap,
  } = useAutomationBootstrap()
  const linkedinConnection = bootstrap?.linkedin ?? null
  const sessions = bootstrap?.sessions ?? {}
  const linkedInBootstrapDone = !bootstrapLoading
  const loading = bootstrapLoading || bootstrapFetching
  const [showLinkedInReconnect, setShowLinkedInReconnect] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)
  const [showTroubleshooting, setShowTroubleshooting] = useState(false)
  const pairingBaselineRef = useRef(null)

  const linkedinSessionReady =
    linkedInBootstrapDone &&
    sessions.linkedin?.status === "ready" &&
    Boolean(linkedinConnection?.connected) &&
    Boolean(linkedinConnection?.sessionHealthy)

  const linkedinSetupComplete =
    linkedinSessionReady && !showLinkedInReconnect && !pairingData?.pairingCode

  const linkedinDaysSinceSync = daysSinceIso(
    linkedinConnection?.lastSyncedAt || sessions.linkedin?.last_saved_at
  )

  const extensionLabel = useMemo(() => {
    if (!linkedInBootstrapDone) return "Checking…"
    if (linkedinSetupComplete) return "Installed & linked"
    if (pairingData?.pairingCode) return "Waiting for connection"
    return "Install on desktop Chrome"
  }, [linkedInBootstrapDone, linkedinSetupComplete, pairingData])

  const stepState = useMemo(() => {
    const active = "active"
    const done = "done"
    const pending = "pending"
    if (linkedinSetupComplete) {
      return { extension: done, code: done, connect: done, active: done }
    }
    if (pairingData?.pairingCode) {
      return { extension: done, code: done, connect: active, active: pending }
    }
    if (linkedinConnection?.connected) {
      return { extension: done, code: active, connect: pending, active: pending }
    }
    return { extension: active, code: pending, connect: pending, active: pending }
  }, [linkedinSetupComplete, pairingData, linkedinConnection])

  const refreshLinkedInState = useCallback(async () => {
    const result = await refetchBootstrap()
    const payload = result.data
    if (payload?.sessions) {
      onSessionsChange?.(payload.sessions)
    }
    return payload
  }, [onSessionsChange, refetchBootstrap])

  useEffect(() => {
    if (bootstrap?.sessions) {
      onSessionsChange?.(bootstrap.sessions)
    }
  }, [bootstrap?.sessions, onSessionsChange])

  useEffect(() => {
    setIsMobileSetupFlow(isMobileOrTabletViewport())
    const onResize = () => setIsMobileSetupFlow(isMobileOrTabletViewport())
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  useEffect(() => {
    if (!pairingData?.pairingCode) return
    const expiresAtMs = pairingData.expiresAt
      ? new Date(pairingData.expiresAt).getTime()
      : Date.now() + (pairingData.expiresIn || 300) * 1000
    const tick = () => {
      const diff = Math.max(0, Math.floor((expiresAtMs - Date.now()) / 1000))
      setPairingSecondsLeft(diff)
      if (diff <= 0) {
        setPairingData(null)
        pairingBaselineRef.current = null
      }
    }
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [pairingData])

  useEffect(() => {
    if (!pairingData?.pairingCode) return
    const pollId = window.setInterval(() => {
      void refreshLinkedInState().catch(() => {})
    }, 3000)
    return () => window.clearInterval(pollId)
  }, [pairingData, refreshLinkedInState])

  useEffect(() => {
    if (!pairingData?.pairingCode || !pairingBaselineRef.current) return
    const baseline = pairingBaselineRef.current
    const nowConnected = Boolean(linkedinConnection?.connected)
    const nowSynced = linkedinConnection?.lastSyncedAt ?? null
    const becameConnected = !baseline.connected && nowConnected
    const syncedAfterCode =
      nowConnected && nowSynced && nowSynced !== baseline.lastSyncedAt
    if (!becameConnected && !syncedAfterCode) return
    setPairingData(null)
    setPairingSecondsLeft(0)
    pairingBaselineRef.current = null
    setShowLinkedInReconnect(false)
    showToast("LinkedIn connected successfully. Automation is now active.")
  }, [linkedinConnection, pairingData, showToast])

  async function handleGeneratePairingCode() {
    setPairingLoading(true)
    try {
      const raw = await generateLinkedInPairingCode()
      const normalized = normalizePairingPayload(raw)
      if (!normalized) throw new Error("Invalid pairing code response.")
      pairingBaselineRef.current = {
        connected: Boolean(linkedinConnection?.connected),
        lastSyncedAt: linkedinConnection?.lastSyncedAt ?? null,
      }
      setPairingData(normalized)
      setPairingSecondsLeft(normalized.expiresIn)
      showToast("Enter this code in Career Lens within 5 minutes.")
    } catch (err) {
      showToast(
        humanizeErrorMessage(
          err instanceof Error ? err.message : "Could not generate pairing code"
        ),
        "error"
      )
    } finally {
      setPairingLoading(false)
    }
  }

  async function handleDisconnect() {
    const confirmed = window.confirm(
      "Disconnect LinkedIn from Career OS? Job imports from LinkedIn will stop until you connect again with a new pairing code."
    )
    if (!confirmed) return
    setDisconnecting(true)
    try {
      await disconnectLinkedIn()
      setPairingData(null)
      setShowLinkedInReconnect(false)
      pairingBaselineRef.current = null
      await refreshLinkedInState()
      showToast("LinkedIn disconnected. Your session was removed.")
    } catch (err) {
      showToast(
        humanizeErrorMessage(err instanceof Error ? err.message : "Disconnect failed"),
        "error"
      )
    } finally {
      setDisconnecting(false)
    }
  }

  const connectionTone = !linkedInBootstrapDone
    ? "neutral"
    : linkedinConnection?.connected
      ? "good"
      : "neutral"
  const healthTone = !linkedInBootstrapDone
    ? "neutral"
    : linkedinConnection?.sessionHealthy
      ? "good"
      : "warn"

  return (
    <section className="rounded-xl border border-border/80 bg-card/50 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Briefcase className="size-5 text-indigo-400" />
          <div>
            <h2 className="font-medium text-foreground">
              {linkedinSetupComplete ? "LinkedIn automation" : "Connect LinkedIn"}
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {linkedinSetupComplete
                ? "Career Lens keeps your session fresh. Jobs import automatically."
                : "One-time desktop setup — then use Career OS on any device."}
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={loading}
          onClick={() => void refreshLinkedInState()}
          aria-label="Refresh status"
        >
          {loading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
        </Button>
      </div>

      <div className="mt-4">
        <TrustCallout />
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <StatusPill
          label="Connection"
          value={
            !linkedInBootstrapDone
              ? "Checking…"
              : linkedinConnection?.connected
                ? "Connected"
                : "Not connected"
          }
          tone={connectionTone}
        />
        <StatusPill
          label="Last synced"
          value={
            linkedInBootstrapDone
              ? formatSavedAt(linkedinConnection?.lastSyncedAt)
              : "—"
          }
        />
        <StatusPill
          label="Session health"
          value={
            !linkedInBootstrapDone
              ? "Checking…"
              : linkedinConnection?.sessionHealthy
                ? "Healthy"
                : "Reconnect needed"
          }
          tone={healthTone}
        />
        <StatusPill
          label="Career Lens"
          value={extensionLabel}
          tone={linkedinSetupComplete ? "good" : pairingData ? "warn" : "neutral"}
        />
      </div>

      {linkedInBootstrapDone && linkedinConnection?.lastFetchAt ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Last job import: {formatSavedAt(linkedinConnection.lastFetchAt)}
          {linkedinConnection.lastFetchJobCount > 0
            ? ` · ${linkedinConnection.lastFetchJobCount} roles`
            : ""}
        </p>
      ) : null}

      {!linkedInBootstrapDone ? (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-border/70 bg-background/40 px-4 py-3 text-sm text-muted-foreground">
          <Loader2 className="size-4 shrink-0 animate-spin" />
          Loading your LinkedIn status…
        </div>
      ) : isMobileSetupFlow ? (
        <div className="mt-4 space-y-4">
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
            <div className="flex items-center gap-2 font-medium text-amber-100">
              <Smartphone className="size-4" />
              Desktop setup required once
            </div>
            <p className="mt-2 text-amber-100/90">
              LinkedIn connection uses the Career Lens Chrome extension on a laptop or desktop.
              After that, scans and jobs sync in the cloud — this app works everywhere.
            </p>
            <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-xs text-amber-100/85">
              <li>On your computer, install Career Lens in Chrome</li>
              <li>Open Career OS → Scans &amp; Automation → Automation</li>
              <li>Generate a pairing code and enter it in Career Lens</li>
              <li>Return here and refresh to see Connected</li>
            </ol>
          </div>
          <LinkedInOnboardingSteps stepState={stepState} />
        </div>
      ) : linkedinSetupComplete ? (
        <div className="mt-4 space-y-3">
          <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm animate-in fade-in duration-300">
            <div className="flex items-center gap-2 font-medium text-emerald-100">
              <CheckCircle2 className="size-4 shrink-0" />
              Automation active
            </div>
            <p className="mt-2 text-emerald-100/90">
              You're all set. Run a scan or use Fetch LinkedIn Jobs to pull in roles. Career
              Lens refreshes your session quietly in the background.
            </p>
            {linkedinDaysSinceSync != null &&
              linkedinDaysSinceSync >= LINKEDIN_RECONNECT_HINT_DAYS && (
                <p className="mt-2 text-xs text-amber-200/90">
                  Last sync was {linkedinDaysSinceSync} days ago. If imports fail, tap
                  Reconnect below.
                </p>
              )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setShowLinkedInReconnect(true)
                setPairingData(null)
              }}
            >
              Reconnect
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="text-destructive hover:text-destructive"
              disabled={disconnecting}
              onClick={handleDisconnect}
            >
              {disconnecting ? (
                <Loader2 className="mr-1 size-3 animate-spin" />
              ) : (
                <Unplug className="mr-1 size-3" />
              )}
              Disconnect
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowTroubleshooting((v) => !v)}
            >
              <HelpCircle className="mr-1 size-3" />
              Help
            </Button>
          </div>
          {showTroubleshooting ? <TroubleshootingHints /> : null}
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          <LinkedInOnboardingSteps stepState={stepState} />

          <div className="rounded-lg border border-border/70 bg-background/40 p-4 text-sm">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <Monitor className="size-4 text-indigo-400" />
              Desktop setup
            </div>
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-xs leading-relaxed text-muted-foreground">
              <li>
                <span className="inline-flex items-center gap-1 text-foreground">
                  <Puzzle className="size-3.5" />
                  Install Career Lens
                </span>{" "}
                — load the extension from your Career OS project folder in Chrome → Extensions
                (Developer mode → Load unpacked), or install from the Chrome Web Store when
                published.
              </li>
              <li>Sign in to LinkedIn in the same Chrome profile.</li>
              <li>Generate a pairing code below (valid for 5 minutes).</li>
              <li>Open Career Lens, enter the code, and tap Connect.</li>
              <li>This page updates automatically when connection succeeds.</li>
            </ol>
            <div className="mt-3 flex flex-wrap gap-2">
              <a
                href={CHROME_EXTENSIONS_URL}
                className="inline-flex items-center gap-1 text-xs text-indigo-300 hover:underline"
              >
                Open Chrome extensions
                <ExternalLink className="size-3" />
              </a>
              <a
                href="https://www.linkedin.com/feed/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-indigo-300 hover:underline"
              >
                Open LinkedIn
                <ExternalLink className="size-3" />
              </a>
            </div>
          </div>

          {showLinkedInReconnect || !linkedinConnection?.sessionHealthy ? (
            <TroubleshootingHints compact />
          ) : null}

          {showLinkedInReconnect ? (
            <p className="text-xs text-muted-foreground">
              Generate a new code if you changed your LinkedIn password or imports stopped
              working.{" "}
              <button
                type="button"
                className="text-foreground underline"
                onClick={() => setShowLinkedInReconnect(false)}
              >
                Cancel
              </button>
            </p>
          ) : null}

          <Button
            type="button"
            onClick={handleGeneratePairingCode}
            disabled={pairingLoading}
          >
            {pairingLoading && <Loader2 className="mr-2 size-4 animate-spin" />}
            Generate pairing code
          </Button>

          {pairingData?.pairingCode ? (
            <div className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 p-4 animate-in fade-in duration-300">
              <p className="text-xs uppercase tracking-wide text-indigo-200">
                Your pairing code
              </p>
              <p className="mt-1 text-3xl font-semibold tracking-[0.25em] text-white">
                {pairingData.pairingCode}
              </p>
              <p className="mt-1 text-xs text-indigo-200">
                {pairingSecondsLeft > 0
                  ? `Expires in ${Math.floor(pairingSecondsLeft / 60)}:${String(
                      pairingSecondsLeft % 60
                    ).padStart(2, "0")}`
                  : "Expired — generate a new code"}
              </p>
              <p className="mt-2 text-xs text-indigo-100/80">
                Open Career Lens → enter this code → Connect. We'll confirm here
                automatically.
              </p>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}

function TroubleshootingHints({ compact = false }) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border/60 bg-muted/15 p-3 text-xs text-muted-foreground",
        compact && "mt-0"
      )}
    >
      <p className="font-medium text-foreground">Quick fixes</p>
      <ul className="mt-2 list-disc space-y-1 pl-4">
        <li>Make sure you're logged into LinkedIn in the same Chrome profile as Career Lens.</li>
        <li>If the code expired, generate a new one (5-minute window).</li>
        <li>In Career Lens, try Resync after logging into LinkedIn.</li>
        <li>Still stuck? Disconnect here, then run setup again from step 1.</li>
      </ul>
      <p className="mt-2">
        More help: Settings → Privacy &amp; automation, or{" "}
        <code className="text-[10px]">docs/product/onboarding-experience.md</code>
      </p>
    </div>
  )
}
