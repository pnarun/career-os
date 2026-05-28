import { useCallback, useEffect, useState } from "react"
import { Link2, Puzzle, Radar, X } from "lucide-react"

import { CareerOsLogo } from "@/components/brand/CareerOsLogo"
import { privacyPolicyHref } from "@/lib/publicRoutes"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const STORAGE_KEY = "career-os-beta-welcome-dismissed"

const STEPS = [
  {
    icon: Puzzle,
    title: "Install Career Lens",
    body: "Load the unpacked extension in Chrome (beta package). Sign in to LinkedIn in the same browser profile.",
  },
  {
    icon: Link2,
    title: "Pair with Career OS",
    body: "In Scans & Automation, generate a 6-digit code and enter it in the extension popup.",
  },
  {
    icon: Radar,
    title: "Run your first scan",
    body: "Set job preferences in Settings, then start a scan. You'll see matches in Jobs and get a summary when it finishes.",
  },
]

export function BetaWelcomeModal({ onNavigate }) {
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState(0)

  useEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_KEY) === "1") return
      setOpen(true)
    } catch {
      setOpen(true)
    }
  }, [])

  const dismiss = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, "1")
    } catch {
      /* ignore */
    }
    setOpen(false)
  }, [])

  if (!open) return null

  const current = STEPS[step]
  const Icon = current.icon

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="beta-welcome-title"
    >
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <CareerOsLogo variant="full" size="sm" className="max-h-8" />
          <button
            type="button"
            className="rounded-md p-1 text-muted-foreground hover:bg-muted"
            onClick={dismiss}
            aria-label="Close"
          >
            <X className="size-5" />
          </button>
        </div>
        <p className="text-xs font-medium uppercase tracking-wide text-indigo-400">Beta welcome</p>
        <h2 id="beta-welcome-title" className="mt-1 text-lg font-semibold text-foreground">
          {current.title}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{current.body}</p>
        <div
          className={cn(
            "mt-5 flex size-12 items-center justify-center rounded-xl",
            "bg-indigo-500/15 text-indigo-300"
          )}
        >
          <Icon className="size-6" aria-hidden />
        </div>
        <div className="mt-6 flex gap-2">
          {step > 0 ? (
            <Button type="button" variant="outline" onClick={() => setStep((s) => s - 1)}>
              Back
            </Button>
          ) : (
            <span />
          )}
          {step < STEPS.length - 1 ? (
            <Button type="button" className="ml-auto" onClick={() => setStep((s) => s + 1)}>
              Next
            </Button>
          ) : (
            <Button
              type="button"
              className="ml-auto"
              onClick={() => {
                dismiss()
                onNavigate?.("operations-hub")
              }}
            >
              Go to automation
            </Button>
          )}
        </div>
        <p className="mt-4 text-center text-xs text-muted-foreground">
          <a
            href={privacyPolicyHref()}
            target="_blank"
            rel="noopener noreferrer"
            className="underline-offset-4 hover:underline"
          >
            Privacy policy
          </a>
        </p>
      </div>
    </div>
  )
}
