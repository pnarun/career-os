import { useEffect } from "react"
import { createPortal } from "react-dom"
import { X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const SIZE_CLASS = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
}

const PLACEMENT_CLASS = {
  center: "items-center justify-center",
  top: "items-start justify-center pt-[calc(var(--app-topbar-height,3.5rem)+0.75rem)] sm:pt-[calc(var(--app-topbar-height,4rem)+1rem)]",
}

const BACKDROP_CLASS = {
  default: "bg-black/50 backdrop-blur-xl backdrop-saturate-150",
  heavy: "bg-black/55 backdrop-blur-2xl backdrop-saturate-150",
  glass: "bg-black/40 backdrop-blur-2xl backdrop-saturate-125",
  light: "bg-white/25 backdrop-blur-2xl backdrop-saturate-150",
  dark: "bg-black/50 backdrop-blur-2xl backdrop-saturate-150",
}

const PANEL_VARIANT_CLASS = {
  app: "border-border/80 bg-card text-card-foreground shadow-2xl shadow-black/40",
  landing:
    "border-slate-200/90 bg-white/95 text-slate-900 shadow-2xl shadow-indigo-900/15 backdrop-blur-md",
  auth: "neon-glass border-indigo-500/25 bg-card/95 text-card-foreground shadow-2xl shadow-black/50",
}

/**
 * App modal (portal). placement: center = auth on landing; top = in-app dialogs.
 */
export function AppModal({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  className,
  panelClassName,
  size = "md",
  placement = "top",
  backdrop = "default",
  panelVariant = "app",
  closeOnBackdrop = true,
  showClose = true,
  "aria-labelledby": ariaLabelledBy,
}) {
  useEffect(() => {
    if (!open) return undefined

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose?.()
    }
    document.addEventListener("keydown", onKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open, onClose])

  if (!open || typeof document === "undefined") return null

  const titleId = ariaLabelledBy || "app-modal-title"

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
      className={cn(
        "fixed inset-0 z-[300] flex p-4 sm:p-6",
        PLACEMENT_CLASS[placement] ?? PLACEMENT_CLASS.top,
        BACKDROP_CLASS[backdrop] ?? BACKDROP_CLASS.default,
        className
      )}
      onMouseDown={(event) => {
        if (closeOnBackdrop && event.target === event.currentTarget) onClose?.()
      }}
    >
      <div
        className={cn(
          "flex max-h-[min(90vh,720px)] w-full flex-col overflow-hidden rounded-2xl border",
          SIZE_CLASS[size] ?? SIZE_CLASS.md,
          PANEL_VARIANT_CLASS[panelVariant] ?? PANEL_VARIANT_CLASS.app,
          panelClassName
        )}
        onMouseDown={(event) => event.stopPropagation()}
      >
        {(title || description || showClose) && (
          <div
            className={cn(
              "flex shrink-0 items-start justify-between gap-3 px-5 py-4",
              title || description
                ? panelVariant === "landing"
                  ? "border-b border-slate-200/80"
                  : "border-b border-border/60"
                : "justify-end pb-0 pt-3"
            )}
          >
            <div className="min-w-0 flex-1">
              {title ? (
                <div id={titleId} className="text-lg font-semibold leading-snug tracking-tight">
                  {title}
                </div>
              ) : null}
              {description ? (
                <p
                  className={cn(
                    "mt-1.5 text-sm leading-relaxed",
                    panelVariant === "landing" ? "text-slate-600" : "text-muted-foreground"
                  )}
                >
                  {description}
                </p>
              ) : null}
            </div>
            {showClose && onClose ? (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className={cn("shrink-0", !title && !description && "-mt-1")}
                aria-label="Close dialog"
                onClick={onClose}
              >
                <X className="size-4" />
              </Button>
            ) : null}
          </div>
        )}

        {children ? (
          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>
        ) : null}

        {footer ? (
          <div
            className={cn(
              "flex shrink-0 flex-col-reverse gap-2 border-t px-5 py-4 sm:flex-row sm:justify-end",
              panelVariant === "landing"
                ? "border-slate-200/80 bg-slate-50/80"
                : "border-border/60 bg-muted/20"
            )}
          >
            {footer}
          </div>
        ) : null}
      </div>
    </div>,
    document.body
  )
}
