import { Loader2 } from "lucide-react"

import { useBackendWake } from "@/context/BackendWakeContext"
import { cn } from "@/lib/utils"

const LABELS = {
  online: "Backend online",
  checking: "Connecting…",
  reconnecting: "Reconnecting…",
  sleeping: "Backend sleeping",
  error: "Backend unavailable",
}

const DOT_CLASS = {
  online: "bg-emerald-400 shadow-emerald-400/50",
  checking: "bg-amber-400 animate-pulse",
  reconnecting: "bg-amber-400 animate-pulse",
  sleeping: "bg-orange-400 animate-pulse",
  error: "bg-red-400",
}

export function BackendStatusIndicator({ className = "", compact = false }) {
  const { status, waking, retryWake } = useBackendWake()
  const label = LABELS[status] ?? status

  return (
    <button
      type="button"
      onClick={() => {
        if (status === "sleeping" || status === "error") void retryWake()
      }}
      className={cn(
        "flex w-full items-center gap-2 rounded-md text-left text-xs text-muted-foreground transition-colors",
        (status === "sleeping" || status === "error") && "hover:text-foreground",
        className
      )}
      title={
        status === "sleeping" || status === "error"
          ? "Click to retry connection"
          : label
      }
    >
      {waking ? (
        <Loader2 className="size-2.5 shrink-0 animate-spin text-amber-400" />
      ) : (
        <span
          className={cn("size-2 shrink-0 rounded-full shadow-sm", DOT_CLASS[status] ?? DOT_CLASS.error)}
          aria-hidden
        />
      )}
      {!compact && <span className="truncate">{label}</span>}
    </button>
  )
}
