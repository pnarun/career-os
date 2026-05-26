import { X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/**
 * App-wide modal anchored top-center (mobile-friendly).
 */
export function TopCenterDialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  className,
  "aria-labelledby": ariaLabelledBy,
}) {
  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={ariaLabelledBy}
      className="fixed inset-0 z-[220] flex justify-center bg-black/60 p-3 pt-6 backdrop-blur-sm sm:p-4 sm:pt-8"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose?.()
      }}
    >
      <div
        className={cn(
          "neon-glass max-h-[min(85vh,640px)] w-full max-w-md overflow-y-auto rounded-2xl p-5 shadow-2xl",
          className
        )}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            {title ? (
              <div className="text-lg font-semibold tracking-tight">{title}</div>
            ) : null}
            {description ? (
              <p className="mt-1 text-sm text-muted-foreground">{description}</p>
            ) : null}
          </div>
          {onClose ? (
            <Button type="button" variant="ghost" size="icon" className="shrink-0" onClick={onClose}>
              <X className="size-4" />
            </Button>
          ) : null}
        </div>
        {children}
        {footer ? <div className="mt-5 flex justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  )
}
