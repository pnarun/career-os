import { memo, useCallback, useEffect, useMemo, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useFeedVersion } from "@/context/RealtimeContext"
import { useDebounce } from "@/hooks/useDebounce"
import { useJobsFeed } from "@/hooks/useJobsFeed"
import { useLatestScanAnalytics } from "@/hooks/useLatestScanAnalytics"
import { VirtualizedJobGrid } from "@/components/VirtualizedJobGrid"
import { queryKeys } from "@/lib/queryKeys"
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
  Search,
  ShieldAlert,
} from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { isDevBuild } from "@/lib/env"
import { cn } from "@/lib/utils"
import { fetchHistoricalJobs } from "@/services/jobDebugService"
import { DebugSummaryPanel } from "@/components/DebugSummaryPanel"
import { JobApplicationActions } from "@/components/JobApplicationActions"
import {
  JobDiscoveryLoading,
  JobDiscoveryLoadingInline,
} from "@/components/JobDiscoveryLoading"
import { JobDescriptionModal } from "@/components/JobDescriptionModal"
import { JobDetailsModal } from "@/components/JobDetailsModal"
import { ProviderFeedSummary } from "@/components/ProviderFeedSummary"
import { ScanAnalyticsPanel } from "@/components/ScanAnalyticsPanel"
import { ScanProgressPanel } from "@/components/scans/ScanProgressPanel"
import { FEED_PROVIDER_OPTIONS, FEED_SORT_OPTIONS } from "@/services/jobFeedService"
import { resolveScanSummary } from "@/utils/providerStatusUtils"
import { fetchJobs, getMatchBadgeVariant } from "@/services/jobService"
import {
  DEFAULT_LOCATION_FILTER,
  buildLocationSummary,
  buildSourceSummary,
  extractLocationFilterOptions,
  filterJobsByLocation,
  getLocationBadgeLabel,
  getLocationBadgeStyle,
  getLocationCategory,
} from "@/utils/jobLocationUtils"
import {
  filterJobsByLocationAndProviders,
} from "@/utils/jobPlatformUtils"
import { ProviderIconBadge } from "@/components/ProviderIconBadge"
import { formatPostedTime } from "@/utils/providerIconUtils"
import { getMatchInsightBadges, getStrengthSummary } from "@/utils/matchInsightUtils"
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

const JobCard = memo(function JobCard({ job, showScanMeta, showQualityDebug, onViewDetails, onViewDescription }) {
  const variant = getMatchBadgeVariant(job.recommendation)
  const locationCategory = getLocationCategory(job)
  const qualityScore = getJobQualityScore(job)
  const qualityBadges = getQualityBadges(job)
  const insightBadges = getMatchInsightBadges(job)
  const strengthSummary = getStrengthSummary(job)
  const showApply = canShowApplyButton(job)
  const rejectionInsight = showQualityDebug ? getQualityRejectionInsight(job) : null
  const postedLabel = formatPostedTime(job.posted_at || job.scan_timestamp)

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <ProviderIconBadge source={job.source} />
              {job.company_tag ? (
                <TagBadge
                  label={job.company_tag}
                  className="bg-violet-500/10 text-violet-300 border-violet-500/30"
                />
              ) : null}
            </div>
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
          {(job.remote_priority || job.job_type === "remote") && (
            <TagBadge
              label="Remote"
              className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            />
          )}
          {job.easy_apply && (
            <TagBadge
              label="Easy Apply"
              className="bg-sky-500/10 text-sky-400 border-sky-500/30"
            />
          )}
          {insightBadges.slice(0, 3).map(({ key, label, className }) => (
            <TagBadge key={key} label={label} className={className} />
          ))}
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
        {postedLabel && (
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="size-3.5 shrink-0" />
            Posted {postedLabel}
          </p>
        )}

        {job.career_fit && (
          <p className="text-xs font-medium text-foreground/90">{job.career_fit}</p>
        )}
        {strengthSummary && (
          <p className="text-xs text-muted-foreground">{strengthSummary}</p>
        )}

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
      <CardFooter className="flex flex-col gap-2 border-t border-border/60 pt-4">
        <JobApplicationActions job={job} iconOnly />
        <Button type="button" variant="secondary" className="w-full" onClick={() => onViewDetails?.(job)}>
          View match analysis
        </Button>
        <Button type="button" variant="outline" className="w-full" onClick={() => onViewDescription?.(job)}>
          Job description
        </Button>
        {showApply ? (
          <Button
            className="w-full"
            variant="outline"
            onClick={() => window.open(job.apply_url, "_blank", "noopener,noreferrer")}
          >
            <ExternalLink className="size-4" />
            {getApplyButtonLabel(job)}
          </Button>
        ) : isJobSuspicious(job) ? (
          <p className="flex w-full items-center justify-center gap-1.5 text-xs text-muted-foreground">
            <ShieldAlert className="size-3.5" />
            Apply unavailable — job flagged suspicious
          </p>
        ) : null}
      </CardFooter>
    </Card>
  )
})

export function Jobs() {
  const queryClient = useQueryClient()
  const [displayJobs, setDisplayJobs] = useState([])
  const [allFeedJobs, setAllFeedJobs] = useState([])
  const [listPage, setListPage] = useState(1)
  const [historicalMode, setHistoricalMode] = useState(false)
  const [locationFilter, setLocationFilter] = useState(DEFAULT_LOCATION_FILTER)
  const [selectedProviders, setSelectedProviders] = useState([])
  const [remoteOnly, setRemoteOnly] = useState(false)
  const [easyApplyOnly, setEasyApplyOnly] = useState(false)
  const [minMatch, setMinMatch] = useState(0)
  const [keyword, setKeyword] = useState("")
  const [sortBy, setSortBy] = useState("default")
  const [scanSummary, setScanSummary] = useState(null)
  const [error, setError] = useState(null)
  const [hasFetched, setHasFetched] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [scanProgressLabel, setScanProgressLabel] = useState("")
  const [liveScanStatus, setLiveScanStatus] = useState(null)
  const [selectedJob, setSelectedJob] = useState(null)
  const [descriptionJob, setDescriptionJob] = useState(null)
  const [companyFilter, setCompanyFilter] = useState("")
  const [strongMatchesOnly, setStrongMatchesOnly] = useState(false)
  const [remoteHighMatch, setRemoteHighMatch] = useState(false)
  const [easyApplyHighMatch, setEasyApplyHighMatch] = useState(false)
  const feedVersion = useFeedVersion()
  const debouncedKeyword = useDebounce(keyword, 400)

  const feedFilters = useMemo(
    () => ({
      providers: selectedProviders,
      remoteOnly,
      easyApplyOnly,
      minMatch: minMatch > 0 ? minMatch : undefined,
      keyword: debouncedKeyword,
      sort: sortBy,
      strongMatchesOnly,
      remoteHighMatch,
      easyApplyHighMatch,
      company: companyFilter.trim() || undefined,
    }),
    [
      selectedProviders,
      remoteOnly,
      easyApplyOnly,
      minMatch,
      debouncedKeyword,
      sortBy,
      strongMatchesOnly,
      remoteHighMatch,
      easyApplyHighMatch,
      companyFilter,
    ]
  )

  const {
    data: feedData,
    isLoading: feedLoading,
    isFetching: feedFetching,
    error: feedError,
    refetch: refetchFeed,
  } = useJobsFeed(feedFilters, { enabled: !historicalMode })

  const { data: scanAnalytics } = useLatestScanAnalytics({ enabled: !historicalMode })

  useEffect(() => {
    if (historicalMode || !feedData) return
    setDisplayJobs(feedData.jobs)
    setAllFeedJobs(feedData.jobs)
    if (feedData.jobs.length > 0) setHasFetched(true)
  }, [feedData, historicalMode])

  useEffect(() => {
    if (feedError) {
      setError(feedError instanceof Error ? feedError.message : "Failed to load jobs feed")
    }
  }, [feedError])

  useEffect(() => {
    if (historicalMode || !feedVersion) return
    queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all })
  }, [feedVersion, historicalMode, queryClient])

  const applyHistoricalFilters = useCallback(
    (jobs) => {
      let result = filterJobsByLocationAndProviders(jobs, locationFilter, selectedProviders)
      if (remoteOnly) {
        result = result.filter(
          (job) => job.remote_priority || job.job_type === "remote"
        )
      }
      if (easyApplyOnly) {
        result = result.filter((job) => job.easy_apply)
      }
      if (minMatch > 0) {
        result = result.filter((job) => (job.match_percentage ?? 0) >= minMatch)
      }
      if (keyword.trim()) {
        const needle = keyword.trim().toLowerCase()
        result = result.filter(
          (job) =>
            job.title?.toLowerCase().includes(needle) ||
            job.company?.toLowerCase().includes(needle) ||
            job.location?.toLowerCase().includes(needle) ||
            (job.description_full || job.description)?.toLowerCase().includes(needle)
        )
      }
      return result
    },
    [locationFilter, selectedProviders, remoteOnly, easyApplyOnly, minMatch, keyword]
  )

  const locationOptions = useMemo(
    () => extractLocationFilterOptions(historicalMode ? displayJobs : allFeedJobs),
    [displayJobs, allFeedJobs, historicalMode]
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

  const filteredJobs = useMemo(() => {
    if (historicalMode) {
      return applyHistoricalFilters(displayJobs)
    }
    return filterJobsByLocation(displayJobs, locationFilter)
  }, [displayJobs, locationFilter, historicalMode, applyHistoricalFilters])

  const feedMeta = useMemo(
    () => ({
      providers: feedData?.providers ?? {},
      duplicates_removed: feedData?.duplicates_removed ?? 0,
      total_jobs: feedData?.total_jobs ?? feedData?.jobs?.length ?? 0,
    }),
    [feedData]
  )

  useEffect(() => {
    setListPage(1)
  }, [
    filteredJobs.length,
    historicalMode,
    locationFilter,
    debouncedKeyword,
    selectedProviders,
  ])

  const loadHistoricalJobs = useCallback(async () => {
    const data = await fetchHistoricalJobs()
    setDisplayJobs(data)
    setHasFetched(true)
    return data
  }, [])

  const [historicalLoading, setHistoricalLoading] = useState(false)

  useEffect(() => {
    if (!historicalMode) return
    setHistoricalLoading(true)
    setError(null)
    loadHistoricalJobs()
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load jobs")
      })
      .finally(() => setHistoricalLoading(false))
  }, [historicalMode, loadHistoricalJobs])

  const onHistoricalToggle = (enabled) => {
    setHistoricalMode(enabled)
    setLocationFilter(DEFAULT_LOCATION_FILTER)
    setSelectedProviders([])
    setRemoteOnly(false)
    setEasyApplyOnly(false)
    setMinMatch(0)
    setKeyword("")
    setSortBy("default")
    setError(null)
    setDisplayJobs([])
  }

  const toggleProvider = (provider) => {
    setSelectedProviders((current) =>
      current.includes(provider)
        ? current.filter((item) => item !== provider)
        : [...current, provider]
    )
  }

  const onFetchJobs = async () => {
    if (historicalMode) return

    setError(null)
    setIsRefreshing(true)
    setScanSummary(null)
    setHasFetched(true)
    setScanProgressLabel("Starting scan…")
    setLiveScanStatus(null)

    try {
      const result = await fetchJobs({
        onProgress: (status) => {
          setLiveScanStatus(status)
          const provider = status.current_provider
          const pct = status.progress ?? 0
          setScanProgressLabel(
            provider
              ? `Scanning ${provider}… ${pct}%`
              : status.status === "processing"
                ? `Matching jobs… ${pct}%`
                : `Fetching jobs… ${pct}%`
          )
        },
      })
      setScanSummary(result)
      setScanAnalytics(
        resolveScanSummary(result, result.scan_summary) ?? result.scan_summary ?? null
      )
      await refetchFeed()
      await queryClient.invalidateQueries({ queryKey: queryKeys.jobs.latestScan() })
      setLocationFilter(DEFAULT_LOCATION_FILTER)
      setSelectedProviders([])
      setRemoteOnly(false)
      setEasyApplyOnly(false)
      setMinMatch(0)
      setKeyword("")
      setSortBy("default")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch jobs")
    } finally {
      setIsRefreshing(false)
      setScanProgressLabel("")
      setLiveScanStatus(null)
    }
  }

  const isFetching = isRefreshing
  const isLoadingJobs =
    !historicalMode
      ? feedLoading && !feedData && !isRefreshing
      : historicalLoading && displayJobs.length === 0
  const isDiscoveringJobs = isFetching || isLoadingJobs
  const resolvedScanSummary = useMemo(
    () => resolveScanSummary(scanSummary, scanAnalytics),
    [scanSummary, scanAnalytics]
  )

  const activeScanId = scanSummary?.scan_id ?? displayJobs[0]?.scan_id
  const activeScanTime =
    scanSummary?.scan_timestamp ?? displayJobs[0]?.scan_timestamp

  const showEmpty = displayJobs.length === 0 && !isDiscoveringJobs
  const showFilterEmpty =
    displayJobs.length > 0 && filteredJobs.length === 0 && !isDiscoveringJobs

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Opportunity Feed</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {historicalMode
              ? "Historical debug — all stored jobs (up to 500)"
              : "Unified multi-provider feed — deduplicated, scored, and ranked"}
          </p>
        </div>
        <div className="flex w-full flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center xl:w-auto xl:justify-end">
          {isDevBuild ? (
            <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
              <input
                type="checkbox"
                checked={historicalMode}
                onChange={(e) => onHistoricalToggle(e.target.checked)}
                className="size-4 rounded border-border"
              />
              <History className="size-4 text-muted-foreground" />
              <span className="whitespace-nowrap">Historical Debug Mode</span>
            </label>
          ) : null}

          <select
            id="location-filter"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            disabled={displayJobs.length === 0 || isLoadingJobs}
            aria-label="Location filter"
            className="h-9 w-full min-w-0 shrink-0 rounded-lg border border-input bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-40"
          >
            {locationOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>

          <Button
            onClick={onFetchJobs}
            disabled={isFetching || historicalMode}
            className="h-9 w-full shrink-0 sm:w-auto sm:min-w-[132px]"
          >
            {isFetching ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Fetching…
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

      {!historicalMode && (
        <ProviderFeedSummary
          providers={feedMeta.providers}
          duplicatesRemoved={feedMeta.duplicates_removed}
          totalJobs={filteredJobs.length}
          rawTotal={displayJobs.length}
        />
      )}

      <Card>
        <CardContent className="flex flex-col gap-4 py-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-end">
            <div className="flex min-w-[200px] flex-1 flex-col gap-1.5">
              <label htmlFor="keyword-search" className="text-xs font-medium text-muted-foreground">
                Search
              </label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  id="keyword-search"
                  type="search"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="Title, company, skills…"
                  className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm"
                />
              </div>
            </div>

            <div className="flex min-w-[160px] flex-col gap-1.5">
              <label htmlFor="company-filter" className="text-xs font-medium text-muted-foreground">
                Company
              </label>
              <input
                id="company-filter"
                type="search"
                value={companyFilter}
                onChange={(e) => setCompanyFilter(e.target.value)}
                placeholder="Amazon, Flipkart…"
                className="h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"
              />
            </div>

            <div className="flex min-w-[140px] flex-col gap-1.5">
              <label htmlFor="sort-filter" className="text-xs font-medium text-muted-foreground">
                Sort
              </label>
              <select
                id="sort-filter"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="h-9 rounded-lg border border-input bg-background px-3 text-sm"
              >
                {FEED_SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex min-w-[120px] flex-col gap-1.5">
              <label htmlFor="min-match" className="text-xs font-medium text-muted-foreground">
                Min match %
              </label>
              <input
                id="min-match"
                type="number"
                min={0}
                max={100}
                value={minMatch}
                onChange={(e) => setMinMatch(Number(e.target.value) || 0)}
                className="h-9 rounded-lg border border-input bg-background px-3 text-sm"
              />
            </div>

            <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
              <input
                type="checkbox"
                checked={remoteOnly}
                onChange={(e) => setRemoteOnly(e.target.checked)}
                className="size-4 rounded border-border"
              />
              Remote only
            </label>

            <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
              <input
                type="checkbox"
                checked={easyApplyOnly}
                onChange={(e) => setEasyApplyOnly(e.target.checked)}
                className="size-4 rounded border-border"
              />
              Easy apply only
            </label>

            <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
              <input
                type="checkbox"
                checked={strongMatchesOnly}
                onChange={(e) => setStrongMatchesOnly(e.target.checked)}
                className="size-4 rounded border-border"
              />
              Strong matches only
            </label>

            <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
              <input
                type="checkbox"
                checked={remoteHighMatch}
                onChange={(e) => setRemoteHighMatch(e.target.checked)}
                className="size-4 rounded border-border"
              />
              Remote + high match
            </label>

            <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm">
              <input
                type="checkbox"
                checked={easyApplyHighMatch}
                onChange={(e) => setEasyApplyHighMatch(e.target.checked)}
                className="size-4 rounded border-border"
              />
              Easy apply + high match
            </label>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">Providers</p>
            <div className="flex flex-wrap gap-2">
              {FEED_PROVIDER_OPTIONS.map((option) => {
                const active = selectedProviders.includes(option.value)
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => toggleProvider(option.value)}
                    className={cn(
                      "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                      active
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-input bg-background text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {option.label}
                  </button>
                )
              })}
              {selectedProviders.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSelectedProviders([])}
                  className="rounded-md border border-dashed border-input px-2.5 py-1 text-xs text-muted-foreground"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {!historicalMode && (scanAnalytics || scanSummary?.scan_summary) && (
        <ScanAnalyticsPanel
          summary={scanSummary?.scan_summary ?? scanAnalytics}
          scanId={activeScanId}
          scanTimestamp={activeScanTime ? formatScanTime(activeScanTime) : undefined}
          displayedCount={filteredJobs.length}
        />
      )}

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
                {scanSummary.sources && (
                  <>
                    {" "}
                    · fetched{" "}
                    {Object.values(scanSummary.sources).reduce((a, b) => a + Number(b), 0)}{" "}
                    raw across sources
                  </>
                )}
              </p>
            )}

            {isFetching && <JobDiscoveryLoadingInline />}
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isDiscoveringJobs && (
        <div className="space-y-2">
          <JobDiscoveryLoading />
          {liveScanStatus ? <ScanProgressPanel status={liveScanStatus} /> : null}
          {scanProgressLabel ? (
            <p className="text-center text-sm text-muted-foreground">{scanProgressLabel}</p>
          ) : null}
        </div>
      )}

      {showEmpty ? (
        <EmptyState
          icon={Globe}
          title={
            historicalMode
              ? "No saved jobs yet"
              : hasFetched
                ? "No matches in this batch"
                : "Your job feed is waiting"
          }
          description={
            historicalMode
              ? "Run Fetch Jobs in normal mode first to build your history."
              : hasFetched
                ? "Try adjusting filters or run another scan. LinkedIn roles appear after Career Lens is connected."
                : "Upload your resume, connect LinkedIn in Scans & Automation, then run Fetch Jobs for your first curated batch."
          }
        />
      ) : showFilterEmpty ? (
        <EmptyState
          icon={Filter}
          title="No jobs for this filter"
          description='Try "All", "Germany", or "Remote" to see more roles from your latest scan.'
        />
      ) : (
        <VirtualizedJobGrid
          jobs={filteredJobs}
          page={listPage}
          onPageChange={(next) => {
            setListPage(next)
            window.scrollTo({ top: 0, behavior: "smooth" })
          }}
          renderCard={(job) => (
            <JobCard
              job={job}
              showScanMeta={historicalMode}
              showQualityDebug={historicalMode}
              onViewDetails={setSelectedJob}
              onViewDescription={setDescriptionJob}
            />
          )}
        />
      )}
      <JobDescriptionModal
        job={descriptionJob}
        open={Boolean(descriptionJob)}
        onClose={() => setDescriptionJob(null)}
      />
      {isDevBuild ? (
        <DebugSummaryPanel
          historicalMode={historicalMode}
          displayJobsCount={displayJobs.length}
          filteredJobsCount={filteredJobs.length}
          locationFilter={locationFilter}
          qualitySummary={qualitySummary}
          locationSummary={locationSummary}
          sourceSummary={sourceSummary}
          scanSummary={scanSummary}
          resolvedScanSummary={resolvedScanSummary}
          feedMeta={feedMeta}
        />
      ) : null}
      <JobDetailsModal
        job={selectedJob}
        open={Boolean(selectedJob)}
        onClose={() => setSelectedJob(null)}
      />
    </div>
  )
}
