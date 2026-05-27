import { Loader2, Sparkles } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { getLoadingMessages } from "@/data/loadingMessages"
import { useSlowLoadingMessages } from "@/hooks/useSlowLoadingMessages"
import { cn } from "@/lib/utils"

function MessageDots({ count, index, className }) {
  if (count <= 1) return null
  return (
    <div className={cn("flex items-center gap-1.5", className)} aria-hidden>
      {Array.from({ length: count }).map((_, dotIndex) => (
        <span
          key={dotIndex}
          className={cn(
            "h-1.5 rounded-full transition-all duration-300",
            dotIndex === index ? "w-5 bg-indigo-400" : "w-1.5 bg-muted-foreground/40"
          )}
        />
      ))}
    </div>
  )
}

function SpinnerIcon({ size = "md" }) {
  const box = size === "sm" ? "size-10" : "size-14"
  const icon = size === "sm" ? "size-5" : "size-8"
  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-full border border-indigo-500/30 bg-indigo-500/10",
        box
      )}
    >
      <Loader2 className={cn("animate-spin text-indigo-400", icon)} aria-hidden />
      <Sparkles
        className="absolute -right-0.5 -top-0.5 size-3.5 text-amber-400 animate-pulse"
        aria-hidden
      />
    </div>
  )
}

/** Full card — Jobs feed, scan center, page loads. */
export function SlowLoadingPanel({
  active,
  messageKey = "generic",
  messages: messagesProp = undefined,
  className,
  minHeight = "220px",
}) {
  const messages = messagesProp ?? getLoadingMessages(messageKey)
  const { showSlow, message, index, count } = useSlowLoadingMessages(active, messages)

  if (!showSlow) return null

  return (
    <Card
      className={cn(
        "border-indigo-500/20 bg-gradient-to-b from-indigo-950/20 to-transparent",
        className
      )}
    >
      <CardContent
        className="flex flex-col items-center justify-center gap-5 py-12 text-center"
        style={{ minHeight }}
      >
        <SpinnerIcon />
        <div className="max-w-lg space-y-2 px-4">
          <p className="text-base font-medium tracking-tight text-foreground">{message.title}</p>
          {message.subtitle ? (
            <p className="text-sm leading-relaxed text-muted-foreground">{message.subtitle}</p>
          ) : null}
        </div>
        <MessageDots count={count} index={index} />
      </CardContent>
    </Card>
  )
}

/** Centered page block (auth boot, lazy routes, scan center initial load). */
export function SlowLoadingPageCenter({
  active,
  messageKey = "page-load",
  messages: messagesProp = undefined,
  className = "",
}) {
  const messages = messagesProp ?? getLoadingMessages(messageKey)
  const { showSlow, message, index, count } = useSlowLoadingMessages(active, messages)

  return (
    <div
      className={cn(
        "flex min-h-[40vh] flex-col items-center justify-center gap-4 px-4 text-center",
        className
      )}
    >
      <SpinnerIcon size="sm" />
      {showSlow ? (
        <>
          <div className="max-w-md space-y-1.5">
            <p className="text-sm font-medium text-foreground">{message.title}</p>
            {message.subtitle ? (
              <p className="text-xs text-muted-foreground">{message.subtitle}</p>
            ) : null}
          </div>
          <MessageDots count={count} index={index} />
        </>
      ) : (
        <p className="text-xs text-muted-foreground">Loading…</p>
      )}
    </div>
  )
}

/** Below form fields / buttons (auth, save). */
export function SlowLoadingFormHint({
  active,
  messageKey = "generic",
  messages: messagesProp = undefined,
  className,
  tone = "dark",
}) {
  const messages = messagesProp ?? getLoadingMessages(messageKey)
  const { showSlow, message } = useSlowLoadingMessages(active, messages)

  if (!showSlow) return null

  const light = tone === "light"

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border px-3 py-2.5",
        light
          ? "border-indigo-300/60 bg-indigo-50"
          : "border-indigo-500/25 bg-indigo-500/10",
        className
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2
        className={cn(
          "mt-0.5 size-4 shrink-0 animate-spin",
          light ? "text-indigo-600" : "text-indigo-400"
        )}
        aria-hidden
      />
      <div className="min-w-0 text-left">
        <p
          className={cn(
            "text-sm font-medium",
            light ? "text-slate-900" : "text-foreground"
          )}
        >
          {message.title}
        </p>
        {message.subtitle ? (
          <p
            className={cn(
              "text-xs",
              light ? "text-slate-600" : "text-muted-foreground"
            )}
          >
            {message.subtitle}
          </p>
        ) : null}
      </div>
    </div>
  )
}

/** Single-line status (toolbars, summary bars). */
export function SlowLoadingInline({
  active,
  messageKey = "generic",
  messages: messagesProp = undefined,
  className,
}) {
  const messages = messagesProp ?? getLoadingMessages(messageKey)
  const { showSlow, message } = useSlowLoadingMessages(active, messages)

  if (!showSlow) return null

  return (
    <p
      className={cn(
        "flex min-w-0 flex-1 items-center gap-2 text-sm text-indigo-200/90",
        className
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="size-3.5 shrink-0 animate-spin text-indigo-400" aria-hidden />
      <span className="truncate">
        <span className="font-medium text-foreground">{message.title}</span>
        {message.subtitle ? (
          <span className="text-muted-foreground"> — {message.subtitle}</span>
        ) : null}
      </span>
    </p>
  )
}
