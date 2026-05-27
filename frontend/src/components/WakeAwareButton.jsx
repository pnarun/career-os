import { Loader2 } from "lucide-react"

import { ActionTooltip } from "@/components/ui/ActionTooltip"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useBackendWake } from "@/context/BackendWakeContext"

const WAKE_HINT = "API waking up"

const WAKE_FAILED_HINT = "Retry wake"

/**
 * CTA button disabled until backend /health is ready. Hover explains why.
 */
export function WakeAwareButton({
  children,
  disabled = false,
  className,
  showWakeSpinner = true,
  hideTooltip = false,
  tooltipSide = "right",
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

  if (!hint || hideTooltip) return button

  return (
    <ActionTooltip label={hint} side={tooltipSide}>
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
