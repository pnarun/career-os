import { useState } from "react"
import { Bug, ChevronDown, ChevronUp, ShieldCheck } from "lucide-react"

import { isDevBuild } from "@/lib/env"
import { ProviderStatusPanel } from "@/components/ProviderStatusPanel"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { getSourceLabel } from "@/utils/jobLocationUtils"

/**
 * @param {{
 *   historicalMode: boolean
 *   displayJobsCount: number
 *   filteredJobsCount: number
 *   locationFilter: string
 *   qualitySummary: Record<string, unknown>
 *   locationSummary: Array<{ label: string, count: number }>
 *   sourceSummary: Array<{ label: string, count: number }>
 *   scanSummary: Record<string, unknown> | null
 *   resolvedScanSummary: Record<string, unknown> | null
 *   feedMeta?: { providers?: Record<string, number>, duplicates_removed?: number, total_jobs?: number }
 *   defaultExpanded?: boolean
 *   className?: string
 * }} props
 */
export function DebugSummaryPanel({
  historicalMode,
  displayJobsCount,
  filteredJobsCount,
  locationFilter,
  qualitySummary,
  locationSummary,
  sourceSummary,
  scanSummary,
  resolvedScanSummary,
  feedMeta,
  defaultExpanded = false,
  className,
}) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  if (!isDevBuild) return null

  const collapsedHint = feedMeta?.providers
    ? `Providers: ${Object.entries(feedMeta.providers)
        .filter(([, count]) => count > 0)
        .map(([key, count]) => `${getSourceLabel({ source: key })} ${count}`)
        .join(" | ")} · Duplicates removed: ${feedMeta.duplicates_removed ?? 0} · Final jobs: ${feedMeta.total_jobs ?? filteredJobsCount}`
    : `${displayJobsCount} loaded · ${filteredJobsCount} shown · ${locationFilter}`

  return (
    <Card className={cn("border-dashed border-amber-500/30 bg-amber-500/5", className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 pb-2">
        <div className="flex min-w-0 items-center gap-2">
          <Bug className="size-4 shrink-0 text-amber-400" />
          <div className="min-w-0">
            <p className="text-sm font-medium">Debug summary</p>
            <p className="truncate text-xs text-muted-foreground">
              {expanded ? "Quality, sources, and provider diagnostics" : collapsedHint}
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
          aria-label={expanded ? "Collapse debug summary" : "Expand debug summary"}
        >
          {expanded ? <ChevronUp className="size-5" /> : <ChevronDown className="size-5" />}
        </Button>
      </CardHeader>

      {expanded && (
        <>
          <CardContent className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Historical Debug Mode</p>
              <p className="font-semibold">{historicalMode ? "ON" : "OFF"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Jobs loaded</p>
              <p className="font-semibold tabular-nums">{displayJobsCount}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Shown (filtered)</p>
              <p className="font-semibold tabular-nums">{filteredJobsCount}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Location filter</p>
              <p className="font-semibold">{locationFilter}</p>
            </div>
          </CardContent>

          {(historicalMode || displayJobsCount > 0) && (
            <CardContent className="grid gap-4 border-t border-border pt-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Avg quality score</p>
                <p className="font-semibold tabular-nums">{qualitySummary.avgQualityScore}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Suspicious in set</p>
                <p className="font-semibold tabular-nums text-red-400">
                  {qualitySummary.suspiciousCount}
                </p>
              </div>
              <div className="flex items-start gap-1.5">
                <ShieldCheck className="mt-0.5 size-4 text-emerald-400" />
                <div>
                  <p className="text-xs text-muted-foreground">Verified / apply-ready</p>
                  <p className="font-semibold tabular-nums">
                    {qualitySummary.verifiedCount} / {qualitySummary.withApplyUrlCount}
                  </p>
                </div>
              </div>
              {scanSummary?.quality_rejected != null && !historicalMode && (
                <div>
                  <p className="text-xs text-muted-foreground">Last scan quality rejected</p>
                  <p className="font-semibold tabular-nums">{scanSummary.quality_rejected}</p>
                </div>
              )}
            </CardContent>
          )}

          {(locationSummary.length > 0 ||
            sourceSummary.length > 0 ||
            resolvedScanSummary ||
            (scanSummary?.sources && Object.keys(scanSummary.sources).length > 0)) && (
            <CardContent className="space-y-3 border-t border-border pt-4 text-sm">
              {locationSummary.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">
                    Locations found
                  </p>
                  <ul className="flex flex-wrap gap-x-3 gap-y-1">
                    {locationSummary.slice(0, 12).map(({ label, count }) => (
                      <li key={label}>
                        <span className="font-medium">{label}</span>
                        <span className="text-muted-foreground"> ({count})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {sourceSummary.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">
                    Sources (loaded jobs)
                  </p>
                  <ul className="flex flex-wrap gap-x-3 gap-y-1">
                    {sourceSummary.map(({ label, count }) => (
                      <li key={label}>
                        <span className="font-medium">{label}</span>
                        <span className="text-muted-foreground"> ({count})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {scanSummary?.sources && Object.keys(scanSummary.sources).length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">
                    Last scan fetch by source
                  </p>
                  <ul className="flex flex-wrap gap-x-3 gap-y-1">
                    {Object.entries(scanSummary.sources).map(([key, count]) => (
                      <li key={key}>
                        <span className="font-medium">{getSourceLabel({ source: key })}</span>
                        <span className="text-muted-foreground"> ({count})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {resolvedScanSummary && (
                <ProviderStatusPanel summary={resolvedScanSummary} className="mt-2" />
              )}
            </CardContent>
          )}
        </>
      )}
    </Card>
  )
}
