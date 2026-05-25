import { useState } from "react"
import { BarChart3, ChevronDown, ChevronUp, Globe2, Layers } from "lucide-react"

import { ProviderStatusPanel } from "@/components/ProviderStatusPanel"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { getSourceBadgeStyle, getSourceLabel } from "@/utils/jobLocationUtils"

function StatCell({ label, value, className }) {
  return (
    <div className={cn("rounded-lg border border-border/60 bg-background/50 px-3 py-2.5", className)}>
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-foreground">{value}</p>
    </div>
  )
}

function SourceBadge({ sourceKey, count, isTop }) {
  const label = getSourceLabel({ source: sourceKey })
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium",
        getSourceBadgeStyle(sourceKey),
        isTop && "ring-1 ring-indigo-400/50"
      )}
    >
      {label}
      <span className="tabular-nums opacity-90">({count})</span>
      {isTop && (
        <span className="rounded bg-indigo-500/20 px-1 py-0.5 text-[10px] text-indigo-300">
          top
        </span>
      )}
    </span>
  )
}

/**
 * @param {{
 *   summary: Record<string, unknown> | null
 *   scanId?: string
 *   scanTimestamp?: string
 *   displayedCount?: number
 *   className?: string
 *   defaultExpanded?: boolean
 * }} props
 */
export function ScanAnalyticsPanel({
  summary,
  scanId,
  scanTimestamp,
  displayedCount = 0,
  className,
  defaultExpanded = false,
}) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  if (!summary) return null

  const sources = summary.sources || {}
  const locations = summary.locations || {}
  const topSource = summary.top_source || ""

  const sourceEntries = Object.entries(sources)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])

  const failedCount = (summary.failed_sources || []).length

  return (
    <div
      className={cn(
        "rounded-xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-background to-background",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3 p-4 pb-0">
        <div className="flex min-w-0 items-center gap-2">
          <BarChart3 className="size-5 shrink-0 text-indigo-400" />
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-foreground">Scan summary</h3>
            <p className="truncate text-xs text-muted-foreground">
              {expanded
                ? "Transparency across platforms and filtering"
                : `${summary.total_fetched ?? 0} fetched · ${summary.qualified_jobs ?? 0} qualified · ${displayedCount} shown${failedCount > 0 ? ` · ${failedCount} provider issues` : ""}`}
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-8 shrink-0 text-muted-foreground hover:text-foreground"
          onClick={() => setExpanded((open) => !open)}
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse scan summary" : "Expand scan summary"}
        >
          {expanded ? <ChevronUp className="size-5" /> : <ChevronDown className="size-5" />}
        </Button>
      </div>

      {expanded && (
        <div className="p-4 pt-3">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCell label="Total fetched" value={summary.total_fetched ?? 0} />
            <StatCell label="Qualified jobs" value={summary.qualified_jobs ?? 0} />
            <StatCell label="Rejected jobs" value={summary.rejected_jobs ?? 0} />
            <StatCell label="Displayed" value={displayedCount} />
          </div>

          {(scanId || scanTimestamp) && (
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              {scanId && (
                <span>
                  Scan ID: <span className="font-mono text-foreground">{scanId}</span>
                </span>
              )}
              {scanTimestamp && (
                <span>
                  Scan time: <span className="text-foreground">{scanTimestamp}</span>
                </span>
              )}
            </div>
          )}

          {sourceEntries.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <Layers className="size-3.5" />
                Source breakdown
              </p>
              <div className="flex flex-wrap gap-2">
                {sourceEntries.map(([key, count]) => (
                  <SourceBadge
                    key={key}
                    sourceKey={key}
                    count={count}
                    isTop={key === topSource}
                  />
                ))}
              </div>
            </div>
          )}

          {Object.keys(locations).length > 0 && (
            <div className="mt-4">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <Globe2 className="size-3.5" />
                Location breakdown
              </p>
              <div className="flex flex-wrap gap-3 text-sm">
                <span>
                  India{" "}
                  <strong className="tabular-nums text-foreground">
                    ({locations.india ?? 0})
                  </strong>
                </span>
                <span>
                  Remote{" "}
                  <strong className="tabular-nums text-foreground">
                    ({locations.remote ?? 0})
                  </strong>
                </span>
                <span>
                  International{" "}
                  <strong className="tabular-nums text-foreground">
                    ({locations.international ?? 0})
                  </strong>
                </span>
              </div>
            </div>
          )}

          <ProviderStatusPanel summary={summary} className="mt-4" />
        </div>
      )}
    </div>
  )
}
