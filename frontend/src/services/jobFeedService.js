import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

/**
 * @param {Response} response
 */
/**
 * @param {Record<string, unknown>} job
 */
export function mapFeedJobToDisplay(job) {
  return {
    id: job.job_id,
    title: job.title,
    company: job.company,
    company_tag: job.company_tag ?? "",
    location: job.location,
    description: job.description,
    apply_url: job.apply_url,
    source: job.source,
    easy_apply: job.easy_apply,
    job_type: job.remote ? "remote" : "",
    remote_priority: job.remote,
    match_percentage: job.match_score ?? 0,
    job_quality_score: job.job_quality_score ?? 0,
    matched_skills: job.matched_skills ?? [],
    missing_skills: job.missing_skills ?? [],
    recommendation: job.recommendation ?? "",
    scan_id: job.scan_id ?? "",
    scan_timestamp: job.scan_timestamp ?? job.posted_at ?? "",
    posted_at: job.posted_at ?? "",
    has_apply_url: job.has_apply_url ?? Boolean(job.apply_url),
    is_suspicious: job.is_suspicious ?? false,
    quality_flags: job.quality_flags ?? [],
    source_priority: job.source_priority ?? 0,
    skills: job.skills ?? [],
    strengths: job.strengths ?? [],
    recommendations: job.recommendations ?? [],
    experience_alignment: job.experience_alignment ?? "",
    career_fit: job.career_fit ?? "",
    why_match: job.why_match ?? [],
    match_breakdown: job.match_breakdown ?? {},
  }
}

/**
 * @param {{
 *   providers?: string[]
 *   remoteOnly?: boolean
 *   easyApplyOnly?: boolean
 *   minMatch?: number
 *   keyword?: string
 *   sort?: string
 *   strongMatchesOnly?: boolean
 *   remoteHighMatch?: boolean
 *   easyApplyHighMatch?: boolean
 * }} [filters]
 */
export async function getJobsFeed(filters = {}) {
  const params = new URLSearchParams()

  if (filters.providers?.length) {
    params.set("providers", filters.providers.join(","))
  }
  if (filters.remoteOnly) params.set("remote_only", "true")
  if (filters.easyApplyOnly) params.set("easy_apply_only", "true")
  if (filters.strongMatchesOnly) params.set("strong_matches_only", "true")
  if (filters.remoteHighMatch) params.set("remote_high_match", "true")
  if (filters.easyApplyHighMatch) params.set("easy_apply_high_match", "true")
  if (filters.minMatch != null && filters.minMatch > 0) {
    params.set("min_match", String(filters.minMatch))
  }
  if (filters.keyword?.trim()) {
    params.set("keyword", filters.keyword.trim())
  }
  if (filters.sort && filters.sort !== "default") {
    params.set("sort", filters.sort)
  }
  if (filters.company?.trim()) {
    params.set("company", filters.company.trim())
  }

  const query = params.toString()
  const response = await apiFetch(`/jobs/feed${query ? `?${query}` : ""}`)

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  const payload = await response.json()
  return {
    ...payload,
    jobs: Array.isArray(payload.jobs)
      ? payload.jobs.map(mapFeedJobToDisplay)
      : [],
  }
}

export const FEED_SORT_OPTIONS = [
  { value: "default", label: "Best match (default)" },
  { value: "match", label: "Match % only" },
  { value: "quality", label: "Quality score" },
  { value: "source_priority", label: "Provider priority" },
  { value: "newest", label: "Newest first" },
]

export const FEED_PROVIDER_OPTIONS = [
  { value: "linkedin", label: "LinkedIn" },
  { value: "instahyre", label: "Instahyre" },
  { value: "naukri", label: "Naukri" },
  { value: "indeed", label: "Indeed" },
  { value: "remoteok", label: "RemoteOK" },
  { value: "arbeitnow", label: "Arbeitnow" },
]
