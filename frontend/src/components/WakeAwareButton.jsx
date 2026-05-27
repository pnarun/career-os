import { Loader2 } from "lucide-react"

import { ActionTooltip } from "@/components/ui/ActionTooltip"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useBackendWake } from "@/context/BackendWakeContext"

const WAKE_HINT = "API waking up"

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
  const { ready, waking } = useBackendWake()
  const waiting = !ready
  const hint = !hideTooltip && waiting && waking ? WAKE_HINT : ""

  const button = (
    <Button
      {...props}
      className={className}
      disabled={disabled || waiting}
      onClick={onClick}
    >
      {waiting && showWakeSpinner ? <Loader2 className="size-4 animate-spin" /> : null}
      {children}
    </Button>
  )

  if (!hint) return button

  return (
    <ActionTooltip label={hint} side={tooltipSide}>
      <span
        className={cn(
          "inline-flex",
          className?.includes("w-full") && "w-full",
          waiting && "[&_button]:pointer-events-none"
        )}
      >
        {button}
      </span>
    </ActionTooltip>
  )
}
