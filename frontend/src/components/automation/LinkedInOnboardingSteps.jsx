import { CheckCircle2, Circle, Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

const STEPS = [
  {
    id: "extension",
    title: "Install Career Lens",
    subtitle: "Chrome extension on your desktop (one-time).",
  },
  {
    id: "code",
    title: "Generate pairing code",
    subtitle: "A secure 6-digit code from this page (valid 5 minutes).",
  },
  {
    id: "connect",
    title: "Connect LinkedIn",
    subtitle: "Enter the code in Career Lens while logged into LinkedIn.",
  },
  {
    id: "active",
    title: "Automation active",
    subtitle: "Jobs sync in the cloud — use Career OS anywhere.",
  },
]

/**
 * @param {{
 *   stepState: { extension: string; code: string; connect: string; active: string }
 * }} props
 */
export function LinkedInOnboardingSteps({ stepState }) {
  return (
    <ol className="grid gap-2 sm:grid-cols-2">
      {STEPS.map((step, index) => {
        const state = stepState[step.id] || "pending"
        const done = state === "done"
        const active = state === "active"
        return (
          <li
            key={step.id}
            className={cn(
              "flex gap-3 rounded-lg border p-3 text-left transition-colors",
              done && "border-emerald-500/35 bg-emerald-500/5",
              active && "border-indigo-500/40 bg-indigo-500/10",
              !done && !active && "border-border/70 bg-background/30"
            )}
          >
            <span className="mt-0.5 shrink-0" aria-hidden>
              {done ? (
                <CheckCircle2 className="size-5 text-emerald-400" />
              ) : active ? (
                <Loader2 className="size-5 animate-spin text-indigo-400" />
              ) : (
                <Circle className="size-5 text-muted-foreground/50" />
              )}
            </span>
            <div className="min-w-0">
              <p className="text-xs font-medium text-muted-foreground">Step {index + 1}</p>
              <p className="text-sm font-medium text-foreground">{step.title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{step.subtitle}</p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
