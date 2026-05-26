import { useId, useState } from "react"

import { cn } from "@/lib/utils"

/**
 * Styled tooltip for icon actions (replaces native browser title tooltips).
 */
export function ActionTooltip({ label, children, side = "top", className }) {
  const [visible, setVisible] = useState(false)
  const id = useId()

  return (
    <span
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      <span aria-describedby={visible ? id : undefined}>{children}</span>
      {visible && label ? (
        <span
          id={id}
          role="tooltip"
          className={cn(
            "pointer-events-none absolute z-50 whitespace-nowrap rounded-md px-2.5 py-1.5",
            "border border-indigo-500/30 bg-slate-900/95 text-xs font-medium text-slate-100",
            "shadow-lg shadow-indigo-950/40 backdrop-blur-sm",
            "animate-in fade-in-0 zoom-in-95 duration-150",
            side === "top" && "bottom-full left-1/2 mb-2 -translate-x-1/2",
            side === "bottom" && "top-full left-1/2 mt-2 -translate-x-1/2",
            side === "left" && "right-full top-1/2 mr-2 -translate-y-1/2",
            side === "right" && "left-full top-1/2 ml-2 -translate-y-1/2"
          )}
        >
          {label}
          <span
            className={cn(
              "absolute size-2 rotate-45 border border-indigo-500/30 bg-slate-900/95",
              side === "top" && "left-1/2 top-full -translate-x-1/2 -translate-y-1/2 border-t-0 border-l-0",
              side === "bottom" && "bottom-full left-1/2 -translate-x-1/2 translate-y-1/2 border-b-0 border-r-0"
            )}
            aria-hidden
          />
        </span>
      ) : null}
    </span>
  )
}
