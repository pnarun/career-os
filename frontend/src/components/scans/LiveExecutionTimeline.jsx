import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react"

import { useRealtime } from "@/context/RealtimeContext"
import { cn } from "@/lib/utils"

const EVENT_ICON = {
  scan_started: Loader2,
  scan_completed: CheckCircle2,
  scan_failed: XCircle,
  email_delivered: CheckCircle2,
  ai_scoring_complete: CheckCircle2,
  jobs_fetched: CheckCircle2,
  provider_status: XCircle,
  automation_finished: CheckCircle2,
}

function iconFor(event) {
  if (event?.data?.status === "failed" || event?.event === "scan_failed") {
    return XCircle
  }
  return EVENT_ICON[event?.event] || Circle
}

export function LiveExecutionTimeline({ className }) {
  const { timeline, connected, clearTimeline } = useRealtime()

  if (!timeline.length) {
    return (
      <div className={cn("rounded-lg border border-dashed border-border/60 p-4 text-center", className)}>
        <p className="text-sm text-muted-foreground">
          {connected ? "Waiting for live automation events…" : "Connecting to live stream…"}
        </p>
      </div>
    )
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Live execution {connected ? "· connected" : "· reconnecting"}
        </p>
        <button
          type="button"
          className="text-[11px] text-muted-foreground hover:text-foreground"
          onClick={clearTimeline}
        >
          Clear
        </button>
      </div>
      <ol className="max-h-64 space-y-1 overflow-y-auto rounded-lg border border-border/60 bg-muted/20 p-3 font-mono text-xs">
        {timeline.map((entry, index) => {
          const Icon = iconFor(entry)
          const spinning = entry.event === "scan_started"
          const failed =
            entry.event === "scan_failed" ||
            entry.event === "provider_status" ||
            entry.data?.status === "failed"
          return (
            <li key={`${entry.timestamp}-${index}`} className="flex items-start gap-2">
              <Icon
                className={cn(
                  "mt-0.5 size-3.5 shrink-0",
                  spinning && "animate-spin text-sky-400",
                  failed && "text-red-400",
                  !spinning && !failed && "text-emerald-400"
                )}
              />
              <span className="text-muted-foreground">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
              <span className="min-w-0 flex-1 text-foreground">{entry.message}</span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
