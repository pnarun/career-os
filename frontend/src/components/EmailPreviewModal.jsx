import { useEffect } from "react"
import { Loader2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/**
 * @param {{
 *   open: boolean
 *   onClose: () => void
 *   previewHtml: string
 *   loading?: boolean
 *   meta?: { jobsCount?: number, scanId?: string, scanTimestamp?: string }
 * }} props
 */
export function EmailPreviewModal({
  open,
  onClose,
  previewHtml,
  loading = false,
  meta = {},
}) {
  useEffect(() => {
    if (!open) return undefined

    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKeyDown)
    document.body.style.overflow = "hidden"

    return () => {
      document.removeEventListener("keydown", onKeyDown)
      document.body.style.overflow = ""
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="email-preview-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        aria-label="Close preview"
        onClick={onClose}
      />

      <div
        className={cn(
          "relative z-10 flex max-h-[90vh] w-full max-w-3xl flex-col",
          "rounded-xl border border-border bg-card shadow-2xl"
        )}
      >
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div>
            <h2 id="email-preview-title" className="text-sm font-semibold">
              Email preview
            </h2>
            <p className="text-xs text-muted-foreground">
              {meta.jobsCount != null
                ? `${meta.jobsCount} jobs · `
                : ""}
              {meta.scanTimestamp || "Latest scan batch"}
            </p>
          </div>
          <Button variant="outline" size="icon" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-[#0f172a] p-4">
          {loading ? (
            <div className="flex min-h-[240px] items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
              Generating preview…
            </div>
          ) : (
            <iframe
              title="Email preview"
              srcDoc={previewHtml}
              className="h-[min(70vh,640px)] w-full rounded-lg border border-slate-700 bg-[#0f172a]"
              sandbox=""
            />
          )}
        </div>

        <div className="border-t border-border px-4 py-3 text-xs text-muted-foreground">
          Preview only — no email is sent from this dialog.
        </div>
      </div>
    </div>
  )
}
