import { Briefcase } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { getSourceLabel } from "@/utils/jobLocationUtils"
import { FEED_PROVIDER_OPTIONS } from "@/services/jobFeedService"

const PROVIDER_ORDER = FEED_PROVIDER_OPTIONS.map((option) => option.value)

/**
 * @param {Record<string, number>} providers
 */
function formatProviderLine(providers) {
  if (!providers || typeof providers !== "object") return "No provider data yet"

  return PROVIDER_ORDER.filter((key) => (providers[key] ?? 0) > 0)
    .map((key) => `${getSourceLabel({ source: key })}: ${providers[key]}`)
    .join(" · ")
}

/**
 * @param {{
 *   providers?: Record<string, number>
 *   duplicatesRemoved?: number
 *   totalJobs?: number
 *   rawTotal?: number
 *   className?: string
 * }} props
 */
export function ProviderFeedSummary({
  providers = {},
  duplicatesRemoved = 0,
  totalJobs = 0,
  rawTotal = 0,
  className,
}) {
  const providerLine = formatProviderLine(providers)

  return (
    <Card className={className}>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Briefcase className="size-4 text-muted-foreground" />
          Unified feed summary
        </div>
        <p className="text-sm text-foreground">{providerLine || "Run Fetch Jobs to populate providers."}</p>
        <p className="text-xs text-muted-foreground">
          Duplicates removed: <span className="font-semibold tabular-nums text-foreground">{duplicatesRemoved}</span>
          {" · "}
          Final feed size: <span className="font-semibold tabular-nums text-foreground">{totalJobs}</span>
          {rawTotal > 0 && totalJobs !== rawTotal && (
            <>
              {" · "}
              {rawTotal} loaded before client filters
            </>
          )}
        </p>
      </CardContent>
    </Card>
  )
}
