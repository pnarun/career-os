import { useCallback, useState } from "react"
import { Copy, LifeBuoy, RefreshCw } from "lucide-react"

import { useAuth } from "@/context/AuthContext"
import { privacyPolicyHref } from "@/lib/publicRoutes"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

function supportIdFromUser(user) {
  const id = user?.id || user?.user_id || user?._id || ""
  if (!id) return "—"
  const raw = String(id).replace(/[^a-zA-Z0-9]/g, "")
  return raw.length >= 8 ? raw.slice(0, 8).toUpperCase() : raw.toUpperCase() || "—"
}

export function BetaSupportSection() {
  const { user } = useAuth()
  const supportId = supportIdFromUser(user)
  const [copied, setCopied] = useState(false)

  const copySupportId = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(supportId)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      /* ignore */
    }
  }, [supportId])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <LifeBuoy className="size-4 text-indigo-400" />
          Beta support &amp; troubleshooting
        </CardTitle>
        <CardDescription>
          Quick fixes before contacting support. Include your support ID when emailing us.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2">
          <span className="text-muted-foreground">Support ID</span>
          <code className="font-mono text-sm font-semibold text-foreground">{supportId}</code>
          <Button type="button" size="sm" variant="outline" className="gap-1.5" onClick={copySupportId}>
            <Copy className="size-3.5" />
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>

        <ol className="list-decimal space-y-2 pl-5 text-muted-foreground">
          <li>
            <strong className="text-foreground">LinkedIn disconnected?</strong> Open Career Lens,
            confirm LinkedIn login, generate a new pairing code in Scans &amp; Automation, and
            connect again.
          </li>
          <li>
            <strong className="text-foreground">Scan stuck?</strong> Wait a few minutes; scans auto-fail
            after prolonged runs. Start a new scan — avoid launching several at once.
          </li>
          <li>
            <strong className="text-foreground">Extension issues?</strong> Use{" "}
            <span className="text-foreground">Copy diagnostics</span> in the Career Lens popup (no
            passwords included).
          </li>
          <li>
            <strong className="text-foreground">Still stuck?</strong> Email{" "}
            <a
              href="mailto:support@career-lens.in"
              className="text-indigo-400 underline-offset-4 hover:underline"
            >
              support@career-lens.in
            </a>{" "}
            with your support ID.
          </li>
        </ol>

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="gap-1.5"
            onClick={() => {
              window.open(privacyPolicyHref(), "_blank", "noopener,noreferrer")
            }}
          >
            Privacy policy
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="size-3.5" />
            Refresh app
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
