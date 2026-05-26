import { useCallback, useEffect, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Shield,
  X,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SlowLoadingFormHint } from "@/components/SlowLoadingStatus"
import { cn } from "@/lib/utils"
import {
  APPLY_STATES,
  cancelAssistedApply,
  confirmAssistedApply,
  jobToApplyPayload,
  pollApplySession,
  screenshotUrl,
  startAssistedApply,
} from "@/services/autoApplyService"

function StateBadge({ state }) {
  const label = APPLY_STATES[state] || state
  const isWaiting = state === "WAITING_CONFIRMATION"
  const isSuccess = state === "SUCCESS"
  const isError = ["FAILED", "CAPTCHA_BLOCKED"].includes(state)

  return (
    <span
      className={cn(
        "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
        isSuccess && "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
        isWaiting && "border-amber-500/40 bg-amber-500/10 text-amber-400",
        isError && "border-red-500/40 bg-red-500/10 text-red-400",
        !isSuccess && !isWaiting && !isError && "border-border bg-muted/40 text-muted-foreground"
      )}
    >
      {label}
    </span>
  )
}

export function ApplyAssistantModal({ job, open, onClose, onComplete }) {
  const [session, setSession] = useState(null)
  const [starting, setStarting] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState(null)

  const handleTerminal = useCallback(
    (finalSession) => {
      if (finalSession.state === "SUCCESS") {
        onComplete?.(finalSession)
      }
    },
    [onComplete]
  )

  useEffect(() => {
    if (!open || !session?.session_id) return undefined
    return pollApplySession(session.session_id, {
      onUpdate: setSession,
      onTerminal: handleTerminal,
    })
  }, [open, session?.session_id, handleTerminal])

  useEffect(() => {
    if (!open) {
      setSession(null)
      setError(null)
      setStarting(false)
      setConfirming(false)
    }
  }, [open])

  const onStart = async () => {
    setStarting(true)
    setError(null)
    try {
      const created = await startAssistedApply(jobToApplyPayload(job))
      setSession(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start apply assistant")
    } finally {
      setStarting(false)
    }
  }

  const onConfirm = async () => {
    if (!session?.session_id) return
    setConfirming(true)
    setError(null)
    try {
      await confirmAssistedApply(session.session_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirmation failed")
    } finally {
      setConfirming(false)
    }
  }

  const onCancel = async () => {
    if (session?.session_id) {
      try {
        await cancelAssistedApply(session.session_id)
      } catch {
        /* ignore */
      }
    }
    onClose()
  }

  if (!open) return null

  const confidencePct = session
    ? Math.round((session.confidence_score || 0) * 100)
    : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">Apply Assistant</h2>
            <p className="text-sm text-muted-foreground">
              Human-in-the-loop — review before submit
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onCancel}>
            <X className="size-4" />
          </Button>
        </div>

        <div className="space-y-4 p-6">
          <div className="rounded-lg border border-border bg-muted/20 p-4">
            <p className="font-medium">{job.title}</p>
            <p className="text-sm text-muted-foreground">{job.company}</p>
          </div>

          <div className="flex items-start gap-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-sm">
            <Shield className="mt-0.5 size-4 shrink-0 text-indigo-400" />
            <p className="text-muted-foreground">
              Career OS will prefill known fields and pause for your explicit confirmation
              before submitting. CAPTCHA triggers immediate stop — no bypass attempted.
            </p>
          </div>

          {!session && (
            <>
              <SlowLoadingFormHint active={starting} messageKey="assisted-apply" />
              <Button onClick={onStart} disabled={starting} className="w-full">
              {starting ? (
                <>
                  <Loader2 className="mr-2 size-4 animate-spin" />
                  Starting assisted apply…
                </>
              ) : (
                "Start Assisted Apply"
              )}
            </Button>
            </>
          )}

          {session && (
            <>
              <div className="flex items-center justify-between">
                <StateBadge state={session.state} />
                {confidencePct !== null && (
                  <span className="text-sm text-muted-foreground">
                    Confidence: {confidencePct}%
                  </span>
                )}
              </div>

              {session.metadata?.manual_click_required &&
                session.state === "WAITING_CONFIRMATION" && (
                  <div className="flex items-start gap-2 rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-sm">
                    <AlertTriangle className="mt-0.5 size-4 shrink-0 text-sky-400" />
                    <p className="text-muted-foreground">
                      A browser window opened with the job page. Click{" "}
                      <strong className="text-foreground">Easy Apply</strong> there manually,
                      then return here to confirm.
                    </p>
                  </div>
                )}

              {session.filled_fields?.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Fields filled</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {session.filled_fields.map((field, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{field.label}</span>
                        <span className="max-w-[60%] truncate font-medium">{field.value}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {session.detected_questions?.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Detected questions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {session.detected_questions.map((q, idx) => (
                      <div key={idx} className="rounded border border-border p-2 text-sm">
                        <p className="font-medium">{q.label}</p>
                        {q.suggested_answer && (
                          <p className="text-muted-foreground">
                            Suggested: {q.suggested_answer}
                          </p>
                        )}
                        {q.requires_confirmation && !q.answered && (
                          <p className="mt-1 text-xs text-amber-400">Needs your review</p>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {session.unknown_questions?.length > 0 && (
                <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-400" />
                  <div>
                    <p className="font-medium text-amber-200">Unknown questions detected</p>
                    <ul className="mt-1 list-inside list-disc text-muted-foreground">
                      {session.unknown_questions.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ul>
                    <p className="mt-2 text-xs">
                      Complete these manually in the browser window, then confirm.
                    </p>
                  </div>
                </div>
              )}

              {session.screenshots?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Screenshots</p>
                  <div className="grid grid-cols-2 gap-2">
                    {session.screenshots.slice(-4).map((path, idx) => (
                      <a
                        key={idx}
                        href={screenshotUrl(path)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block overflow-hidden rounded border border-border"
                      >
                        <img
                          src={screenshotUrl(path)}
                          alt={`Apply step ${idx + 1}`}
                          className="h-24 w-full object-cover object-top"
                        />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {session.state === "WAITING_CONFIRMATION" && (
                <div className="flex flex-wrap gap-2 pt-2">
                  <Button onClick={onConfirm} disabled={confirming} className="flex-1">
                    {confirming ? (
                      <Loader2 className="mr-2 size-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="mr-2 size-4" />
                    )}
                    Confirm & Submit
                  </Button>
                  <Button variant="outline" onClick={onCancel}>
                    Cancel
                  </Button>
                </div>
              )}

              {session.state === "SUCCESS" && (
                <div className="flex items-center gap-2 text-sm text-emerald-400">
                  <CheckCircle2 className="size-4" />
                  Application submitted and tracked.
                </div>
              )}

              {session.error && (
                <p className="text-sm text-destructive">{session.error}</p>
              )}
            </>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
      </div>
    </div>
  )
}
