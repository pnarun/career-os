import { Loader2 } from "lucide-react"

import { ActionTooltip } from "@/components/ui/ActionTooltip"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useBackendWake } from "@/context/BackendWakeContext"

const WAKE_HINT =
  "Our API is waking up from sleep (Render cold start). This usually takes 30–90 seconds on first visit. Please wait…"

const WAKE_FAILED_HINT =
  "Could not reach the API. Click to retry waking the server, or try again in a minute."

/**
 * CTA button disabled until backend /health is ready. Hover explains why.
 */
export function WakeAwareButton({
  children,
  disabled = false,
  className,
  showWakeSpinner = true,
  onClick,
  ...props
}) {
  const { ready, waking, failed, retryWake } = useBackendWake()
  const blocked = !ready
  const hint = failed ? WAKE_FAILED_HINT : waking || blocked ? WAKE_HINT : ""

  const handleClick = (event) => {
    if (failed) {
      event.preventDefault()
      void retryWake()
      return
    }
    onClick?.(event)
  }

  const button = (
    <Button
      {...props}
      className={className}
      disabled={disabled || (blocked && !failed)}
      onClick={handleClick}
    >
      {(waking || (blocked && !failed)) && showWakeSpinner ? (
        <Loader2 className="size-4 animate-spin" />
      ) : null}
      {children}
    </Button>
  )

  if (!hint) return button

  return (
    <ActionTooltip label={hint} side="top">
      <span
        className={cn(
          "inline-flex",
          className?.includes("w-full") && "w-full",
          blocked && !failed && "[&_button]:pointer-events-none"
        )}
      >
        {button}
      </span>
    </ActionTooltip>
  )
}
