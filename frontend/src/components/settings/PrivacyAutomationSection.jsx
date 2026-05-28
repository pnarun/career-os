import { useCallback, useEffect, useState } from "react"
import {
  CheckCircle2,
  Loader2,
  Shield,
  Unplug,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  disconnectLinkedIn,
  getLinkedInAutomationStatus,
} from "@/services/automationService"
import { humanizeErrorMessage } from "@/lib/userFacingErrors"

const TRUST_POINTS = [
  {
    title: "What Career Lens accesses",
    body: "Your LinkedIn login session only — so we can fetch job listings you already see when logged in.",
  },
  {
    title: "What we never access",
    body: "Passwords, browsing history, messages, feed content, or anything outside linkedin.com session cookies.",
  },
  {
    title: "What we store",
    body: "An encrypted browser session tied to your account, used only for job discovery automation.",
  },
  {
    title: "What we don't store",
    body: "Your LinkedIn password, unrelated cookies, or personal messages.",
  },
]

export function PrivacyAutomationSection() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [disconnecting, setDisconnecting] = useState(false)
  const [feedback, setFeedback] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getLinkedInAutomationStatus()
      setStatus(data)
    } catch {
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleDisconnect() {
    const ok = window.confirm(
      "Disconnect LinkedIn from Career OS? Job imports from LinkedIn will stop until you connect again from Scans & Automation."
    )
    if (!ok) return
    setDisconnecting(true)
    setFeedback(null)
    try {
      await disconnectLinkedIn()
      await load()
      setFeedback({
        type: "success",
        text: "LinkedIn disconnected. Your session was removed from our servers.",
      })
    } catch (err) {
      setFeedback({
        type: "error",
        text: humanizeErrorMessage(
          err instanceof Error ? err.message : "Disconnect failed"
        ),
      })
    } finally {
      setDisconnecting(false)
    }
  }

  const connected = Boolean(status?.connected)

  return (
    <Card id="privacy-automation">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Shield className="size-5 text-indigo-400" />
          <CardTitle className="text-base">Privacy &amp; automation</CardTitle>
        </div>
        <CardDescription>
          How Career Lens and LinkedIn automation work — and how you stay in control.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <ul className="space-y-3 text-sm">
          {TRUST_POINTS.map((item) => (
            <li key={item.title} className="rounded-lg border border-border/60 bg-muted/10 px-3 py-2.5">
              <p className="font-medium text-foreground">{item.title}</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{item.body}</p>
            </li>
          ))}
        </ul>

        <div className="rounded-lg border border-border/70 bg-background/40 p-4 text-sm">
          <p className="font-medium text-foreground">Disconnect anytime</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Disconnecting removes your saved LinkedIn session from Career OS. You can also
            disconnect from the Career Lens extension. To use LinkedIn imports again, complete
            the one-time desktop setup in{" "}
            <span className="text-foreground">Scans &amp; Automation → Automation</span>.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {loading ? (
              <span className="inline-flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="size-3.5 animate-spin" />
                Checking connection…
              </span>
            ) : connected ? (
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
                <CheckCircle2 className="size-3.5" />
                LinkedIn connected
              </span>
            ) : (
              <span className="text-xs text-muted-foreground">LinkedIn not connected</span>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="text-destructive hover:text-destructive"
              disabled={!connected || disconnecting}
              onClick={handleDisconnect}
            >
              {disconnecting ? (
                <Loader2 className="mr-1 size-3.5 animate-spin" />
              ) : (
                <Unplug className="mr-1 size-3.5" />
              )}
              Delete LinkedIn session
            </Button>
          </div>
          {feedback ? (
            <p
              className={
                feedback.type === "success"
                  ? "mt-2 text-xs text-emerald-400"
                  : "mt-2 text-xs text-destructive"
              }
            >
              {feedback.text}
            </p>
          ) : null}
        </div>

        <p className="text-[11px] text-muted-foreground">
          Full extension privacy details are in{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-[10px]">extension/PRIVACY.md</code>{" "}
          in the project repository (also used for the Chrome Web Store listing).
        </p>
      </CardContent>
    </Card>
  )
}
