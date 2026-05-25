import { useEffect, useState } from "react"
import { Download, X } from "lucide-react"

import { Button } from "@/components/ui/button"

export function PwaInstallPrompt() {
  const [deferred, setDeferred] = useState(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (localStorage.getItem("career_os_pwa_dismissed") === "1") {
      setDismissed(true)
    }

    const handler = (event) => {
      event.preventDefault()
      setDeferred(event)
    }
    window.addEventListener("beforeinstallprompt", handler)
    return () => window.removeEventListener("beforeinstallprompt", handler)
  }, [])

  if (dismissed || !deferred) return null

  const install = async () => {
    await deferred.prompt()
    setDeferred(null)
  }

  const dismiss = () => {
    localStorage.setItem("career_os_pwa_dismissed", "1")
    setDismissed(true)
    setDeferred(null)
  }

  return (
    <div className="fixed bottom-20 left-4 right-4 z-[90] mx-auto max-w-md rounded-lg border border-primary/30 bg-background p-4 shadow-lg lg:bottom-6">
      <div className="flex items-start gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Download className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">Install Career OS</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Add to your home screen for quick access and standalone app mode.
          </p>
          <div className="mt-3 flex gap-2">
            <Button size="sm" onClick={install}>
              Install
            </Button>
            <Button size="sm" variant="ghost" onClick={dismiss}>
              Not now
            </Button>
          </div>
        </div>
        <button type="button" className="text-muted-foreground" onClick={dismiss} aria-label="Close">
          <X className="size-4" />
        </button>
      </div>
    </div>
  )
}
