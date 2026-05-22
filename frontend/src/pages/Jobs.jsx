import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  Briefcase,
  Clock,
  ExternalLink,
  Filter,
  Globe,
  History,
  Loader2,
  MapPin,
  RefreshCw,
  ScanLine,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { fetchHistoricalJobs } from "@/services/jobDebugService"
import { fetchJobs, getJobs, getMatchBadgeVariant } from "@/services/jobService"
import {
  DEFAULT_LOCATION_FILTER,
  buildLocationSummary,
  buildSourceSummary,
  extractLocationFilterOptions,
  filterJobsByLocation,
  getLocationBadgeLabel,
  getLocationBadgeStyle,
  getLocationCategory,
  getSourceBadgeStyle,
  getSourceLabel,
} from "@/utils/jobLocationUtils"
import {
  buildQualityDebugSummary,
  canShowApplyButton,
  getApplyButtonLabel,
  getJobQualityScore,
  getQualityBadges,
  getQualityRejectionInsight,
  getQualityScoreStyle,
  isJobSuspicious,
} from "@/utils/jobQualityUtils"

const matchBadgeStyles = {
  excellent: "bg-green-500/15 text-green-400 border-green-500/30",
  strong: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  moderate: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  weak: "bg-red-500/15 text-red-400 border-red-500/30",
  default: "bg-muted text-muted-foreground border-border",
}

function formatScanTime(iso) {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

function TagBadge({ label, className }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
        className
      )}
    >
      {label}
    </span>
  )
}

function MatchBadge({ recommendation }) {
  const variant = getMatchBadgeVariant(recommendation)
  return (
    <TagBadge label={recommendation || "No match"} className={matchBadgeStyles[variant]} />
  )
}

function SkillTags({ items, variant }) {
  if (!items?.length) {
    return <span className="text-xs text-muted-foreground">—</span>
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.slice(0, 8).map((skill) => (
        <span
          key={skill}
          className={cn(
            "rounded px-2 py-0.5 text-xs",
            variant === "matched" && "bg-green-500/10 text-green-400",
            variant === "missing" && "bg-amber-500/10 text-amber-400"
          )}
        >
          {skill}
        </span>
      ))}
      {items.length > 8 && (
        <span className="text-xs text-muted-foreground">+{items.length - 8}</span>
      )}
    </div>
  )
}

function JobCard({ job, showScanMeta, showQualityDebug }) {
  const variant = getMatchBadgeVariant(job.recommendation)
  const locationCategory = getLocationCategory(job)
  const sourceLabel = getSourceLabel(job)
  const qualityScore = getJobQualityScore(job)
  const qualityBadges = getQualityBadges(job)
  const showApply = canShowApplyButton(job)
  const rejectionInsight = showQualityDebug ? getQualityRejectionInsight(job) : null

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-base leading-snug">{job.title}</CardTitle>
            <CardDescription className="font-medium text-foreground/80">
              {job.company}
            </CardDescription>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <div
              className={cn(
                "flex size-12 flex-col items-center justify-center rounded-lg border text-sm font-bold tabular-nums",
                matchBadgeStyles[variant]
              )}
            >
              {job.match_percentage ?? 0}%
            </div>
            {qualityScore > 0 && (
              <span
                className={cn(
                  "rounded border px-1.5 py-0.5 text-[10px] font-semibold tabular-nums",
                  getQualityScoreStyle(qualityScore)
                )}
              >
                Q{qualityScore}
              </span>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {job.recommendation && (
            <MatchBadge recommendation={job.recommendation} />
          )}
          <TagBadge
            label={getLocationBadgeLabel(job)}
            className={getLocationBadgeStyle(locationCategory)}
          />
          <TagBadge
            label={sourceLabel}
            className={getSourceBadgeStyle(String(job.source || ""))}
          />
          {qualityBadges.map(({ key, label, className }) => (
            <TagBadge key={key} label={label} className={className} />
          ))}
          {showScanMeta && job.scan_id && (
            <span className="font-mono text-[10px] text-muted-foreground">
              {job.scan_id}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-3 text-sm">
        <p className="flex items-center gap-1.5 text-muted-foreground">
          <MapPin className="size-3.5 shrink-0" />
          {job.location || "Remote"}
          {job.job_type ? ` · ${job.job_type}` : ""}
        </p>

        {showQualityDebug && (
          <div className="rounded-md border border-dashed border-amber-500/30 bg-amber-500/5 px-2.5 py-2 text-xs">
            <p className="font-medium text-foreground/90">Quality debug</p>
            <p className="mt-1 text-muted-foreground">
              Score: <span className="font-semibold text-foreground">{qualityScore}</span>
              {" · "}
              Suspicious:{" "}
              <span className={isJobSuspicious(job) ? "text-red-400" : "text-green-400"}>
                {isJobSuspicious(job) ? "yes" : "no"}
              </span>
            </p>
            {Array.isArray(job.quality_flags) && job.quality_flags.length > 0 && (
              <p className="mt-1 text-muted-foreground">
                Flags: {job.quality_flags.join(", ")}
              </p>
            )}
            {rejectionInsight && (
              <p className="mt-1 text-amber-400">Would reject: {rejectionInsight}</p>
            )}
          </div>
        )}

        {job.matched_skills && (
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Matched skills</p>
            <SkillTags items={job.matched_skills} variant="matched" />
          </div>
        )}
        {job.missing_skills && (
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Missing skills</p>
            <SkillTags items={job.missing_skills} variant="missing" />
          </div>
        )}
      </CardContent>
      {showApply ? (
        <CardFooter>
          <Button
            className="w-full"
            variant="outline"
            onClick={() => window.open(job.apply_url, "_blank", "noopener,noreferrer")}
          >
            <ExternalLink className="size-4" />
            {getApplyButtonLabel(job)}
          </Button>
        </CardFooter>
      ) : isJobSuspicious(job) ? (
        <CardFooter>
          <p className="flex w-full items-center justify-center gap-1.5 text-xs text-muted-foreground">
            <ShieldAlert className="size-3.5" />
            Apply unavailable — job flagged suspicious
          </p>
        </CardFooter>
      ) : null}
    </Card>
  )
}

export function Jobs() {
  const [displayJobs, setDisplayJobs] = useState([])
  const [historicalMode, setHistoricalMode] = useState(false)
  const [locationFilter, setLocationFilter] = useState(DEFAULT_LOCATION_FILTER)
  const [status, setStatus] = useState("idle")
  const [scanSummary, setScanSummary] = useState(null)
  const [error, setError] = useState(null)
  const [hasFetched, setHasFetched] = useState(false)

  const locationOptions = useMemo(
    () => extractLocationFilterOptions(displayJobs),
    [displayJobs]
  )

  const locationSummary = useMemo(
    () => buildLocationSummary(displayJobs),
    [displayJobs]
  )

  const sourceSummary = useMemo(
    () => buildSourceSummary(displayJobs),
    [displayJobs]
  )

  const qualitySummary = useMemo(
    () => buildQualityDebugSummary(displayJobs),
    [displayJobs]
  )

  const filteredJobs = useMemo(
    () => filterJobsByLocation(displayJobs, locationFilter),
    [displayJobs, locationFilter]
  )

  const loadLatestScan = useCallback(async () => {
    const data = await getJobs()
    setDisplayJobs(data)
    if (data.length > 0) {
      setHasFetched(true)
    }
    return data
  }, [])

  const loadHistoricalJobs = useCallback(async () => {
    const data = await fetchHistoricalJobs()
    setDisplayJobs(data)
    setHasFetched(true)
    return data
  }, [])

  const loadDisplayJobs = useCallback(async () => {
    if (historicalMode) {
      return loadHistoricalJobs()
    }
    return loadLatestScan()
  }, [historicalMode, loadHistoricalJobs, loadLatestScan])

  useEffect(() => {
    setStatus("loading")
    loadDisplayJobs()
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load jobs")
      })
      .finally(() => setStatus("idle"))
  }, [loadDisplayJobs])

  const onHistoricalToggle = (enabled) => {
    setHistoricalMode(enabled)
    setLocationFilter(DEFAULT_LOCATION_FILTER)
    setError(null)
    setStatus("loading")
    setDisplayJobs([])

    const loader = enabled ? loadHistoricalJobs : loadLatestScan
    loader()
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load jobs")
      })
      .finally(() => setStatus("idle"))
  }

  const onFetchJobs = async () => {
    if (historicalMode) return

    setError(null)
    setStatus("loading")
    setScanSummary(null)
    setDisplayJobs([])
    setHasFetched(true)

    try {
      const result = await fetchJobs()
      setScanSummary(result)
      const latest = await getJobs()
      setDisplayJobs(latest)
      setLocationFilter(DEFAULT_LOCATION_FILTER)
      setStatus("success")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch jobs")
      setStatus("error")
    }
  }

  const isFetching = status === "loading"
  const isLoadingJobs = status === "loading" && displayJobs.length === 0
  const activeScanId = scanSummary?.scan_id ?? displayJobs[0]?.scan_id
  const activeScanTime =
    scanSummary?.scan_timestamp ?? displayJobs[0]?.scan_timestamp

  const showEmpty = displayJobs.length === 0 && !isLoadingJobs
  const showFilterEmpty =
    displayJobs.length > 0 && filteredJobs.length === 0 && !isLoadingJobs

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Opportunity Feed</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {historicalMode
              ? "Historical debug — all stored jobs (up to 500)"
              : "Latest scan batch — quality-ranked, apply-validated jobs"}
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
            <input
              type="checkbox"
              checked={historicalMode}
              onChange={(e) => onHistoricalToggle(e.target.checked)}
              className="size-4 rounded border-border"
            />
            <History className="size-4 text-muted-foreground" />
            <span>Historical Debug Mode</span>
          </label>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="location-filter"
              className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"
            >
              <Filter className="size-3.5" />
              Location Filter
            </label>
            <select
              id="location-filter"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              disabled={displayJobs.length === 0 || isLoadingJobs}
              className="h-9 min-w-[140px] rounded-lg border border-input bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {locationOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <Button onClick={onFetchJobs} disabled={isFetching || historicalMode}>
            {isFetching ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Running scan…
              </>
            ) : (
              <>
                <RefreshCw className="size-4" />
                Fetch Jobs
              </>
            )}
          </Button>
        </div>
      </div>

      <Card className="border-dashed border-amber-500/30 bg-amber-500/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Debug summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs text-muted-foreground">Historical Debug Mode</p>
            <p className="font-semibold">{historicalMode ? "ON" : "OFF"}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Jobs loaded</p>
            <p className="font-semibold tabular-nums">{displayJobs.length}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Shown (filtered)</p>
            <p className="font-semibold tabular-nums">{filteredJobs.length}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Location filter</p>
            <p className="font-semibold">{locationFilter}</p>
          </div>
        </CardContent>
        {(historicalMode || displayJobs.length > 0) && (
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
        {(locationSummary.length > 0 || sourceSummary.length > 0) && (
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
                <p className="mb-1 text-xs font-medium text-muted-foreground">Sources</p>
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
          </CardContent>
        )}
      </Card>

      {!historicalMode && (
        <Card>
          <CardContent className="flex flex-col gap-4 py-4 sm:flex-row sm:flex-wrap sm:items-center">
            <div className="flex items-center gap-2">
              <Briefcase className="size-4 text-muted-foreground" />
              <span className="text-sm">
                <span className="font-semibold tabular-nums">{filteredJobs.length}</span>
                <span className="text-muted-foreground">
                  {" "}
                  shown · {displayJobs.length} in latest scan
                </span>
              </span>
            </div>

            {activeScanId && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ScanLine className="size-4 shrink-0" />
                <span className="font-mono text-xs text-foreground">{activeScanId}</span>
              </div>
            )}

            {activeScanTime && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="size-4 shrink-0" />
                <span>{formatScanTime(activeScanTime)}</span>
              </div>
            )}

            {scanSummary && (
              <p className="text-sm text-muted-foreground">
                Stored {scanSummary.stored} new · {scanSummary.skipped_already_shown ?? 0}{" "}
                already shown · {scanSummary.filtered ?? 0} location/engineering filtered ·{" "}
                {scanSummary.quality_rejected ?? 0} quality rejected
              </p>
            )}

            {isFetching && (
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-3.5 animate-spin" />
                Building fresh scan batch…
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isLoadingJobs && (
        <Card>
          <CardContent className="flex min-h-[120px] items-center justify-center gap-2 py-8">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Loading jobs…</span>
          </CardContent>
        </Card>
      )}

      {showEmpty ? (
        <Card>
          <CardContent className="flex min-h-[200px] flex-col items-center justify-center gap-2 py-10 text-center">
            <Globe className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {historicalMode
                ? "No historical jobs in MongoDB yet. Run Fetch Jobs in normal mode first."
                : hasFetched
                  ? "No fresh high-quality India/remote engineering jobs passed quality validation."
                  : "Upload a resume, then run Fetch Jobs to generate your first curated batch."}
            </p>
          </CardContent>
        </Card>
      ) : showFilterEmpty ? (
        <Card>
          <CardContent className="flex min-h-[160px] flex-col items-center justify-center gap-2 py-10 text-center">
            <Filter className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No jobs found for selected location filter.
            </p>
            <p className="text-xs text-muted-foreground">
              Try &quot;All&quot;, &quot;Germany&quot;, or &quot;Remote&quot; to inspect datasets.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filteredJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              showScanMeta={historicalMode}
              showQualityDebug={historicalMode}
            />
          ))}
        </div>
      )}
    </div>
  )
}
