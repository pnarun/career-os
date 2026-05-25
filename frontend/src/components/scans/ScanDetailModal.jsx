import { useEffect, useState } from "react"
import { Loader2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { getScanSessionDetail } from "@/services/scansService"

export function ScanDetailModal({ open, onClose, row }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open || !row?.scanId) {
      setDetail(null)
      return
    }
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const data = await getScanSessionDetail(row.scanId)
        if (!cancelled) setDetail(data)
      } catch {
        if (!cancelled) setDetail(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [open, row?.scanId])

  if (!open) return null

  const summary = row?.raw || {}
  const sources = detail?.source_breakdown || summary.sources || {}
  const failed = detail?.failed_sources || summary.failed_sources || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button type="button" className="absolute inset-0 bg-black/60" aria-label="Close" onClick={onClose} />
      <div className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background shadow-xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-border bg-background px-4 py-3">
          <div>
            <h3 className="font-semibold">Scan details</h3>
            <p className="font-mono text-xs text-muted-foreground">{row?.scanId}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </div>

        <div className="space-y-4 p-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <section>
                <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Overview</p>
                <ul className="grid gap-1 text-sm sm:grid-cols-2">
                  <li>Status: {row?.status}</li>
                  <li>Started: {row?.started}</li>
                  <li>Jobs fetched: {detail?.total_fetched ?? row?.jobsFetched}</li>
                  <li>Qualified: {detail?.qualified_jobs ?? row?.qualifiedJobs}</li>
                  <li>Rejected: {detail?.rejected_jobs ?? "—"}</li>
                  <li>Duplicates removed: {detail?.duplicates_removed ?? "—"}</li>
                </ul>
              </section>

              <section>
                <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Provider results</p>
                <ul className="space-y-1 text-sm">
                  {Object.entries(sources).map(([name, count]) => (
                    <li key={name} className="flex justify-between rounded-md bg-muted/20 px-2 py-1">
                      <span className="capitalize">{name}</span>
                      <span className="tabular-nums">{count} jobs</span>
                    </li>
                  ))}
                </ul>
              </section>

              {failed.length > 0 && (
                <section>
                  <p className="mb-2 text-xs font-medium uppercase text-destructive">Failed providers</p>
                  <ul className="text-sm text-destructive">
                    {failed.map((p) => (
                      <li key={p}>• {p}</li>
                    ))}
                  </ul>
                  {detail?.source_errors && (
                    <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                      {Object.entries(detail.source_errors).map(([src, err]) => (
                        <li key={src}>
                          <span className="capitalize">{src}</span>: {err}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              )}

              <section>
                <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Execution timeline</p>
                <ol className="space-y-1 text-xs text-muted-foreground">
                  <li>1. Scan initiated</li>
                  <li>2. Providers fetched ({Object.keys(sources).length} active)</li>
                  <li>3. Jobs deduplicated and scored</li>
                  <li>4. Batch stored as latest scan</li>
                  {row?.emailSent === "Yes" && <li>5. Digest email sent</li>}
                </ol>
              </section>

              {(detail?.provider_status || summary.provider_status)?.length > 0 && (
                <section>
                  <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Provider diagnostics</p>
                  <ul className="max-h-40 space-y-1 overflow-y-auto text-xs">
                    {(detail?.provider_status || summary.provider_status).map((p) => (
                      <li key={p.source} className="rounded bg-muted/20 px-2 py-1">
                        <span className="capitalize">{p.source}</span>: {p.status}
                        {p.error_message ? ` — ${p.error_message}` : ""}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
