import { Bell, X } from "lucide-react"

import { useRealtimeToasts } from "@/context/RealtimeContext"
import { cn } from "@/lib/utils"

export function RealtimeToastHost() {
  const { toasts, dismissToast } = useRealtimeToasts()

  if (!toasts.length) return null

  return (
    <div className="pointer-events-none fixed bottom-20 right-4 z-[100] flex max-w-sm flex-col gap-2 lg:bottom-6">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "pointer-events-auto flex gap-3 rounded-lg border border-border bg-background/95 p-3 shadow-lg backdrop-blur-sm",
            toast.priority === "high" && "border-amber-500/40 bg-amber-500/5"
          )}
        >
          <div
            className={cn(
              "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full",
              toast.priority === "high"
                ? "bg-amber-500/15 text-amber-600"
                : "bg-primary/15 text-primary"
            )}
          >
            <Bell className="size-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium leading-tight">{toast.title}</p>
            {toast.message ? (
              <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{toast.message}</p>
            ) : null}
          </div>
          <button
            type="button"
            className="shrink-0 rounded p-1 text-muted-foreground hover:bg-muted"
            aria-label="Dismiss"
            onClick={() => dismissToast(toast.id)}
          >
            <X className="size-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}
