/** @typedef {'india' | 'remote' | 'international'} LocationCategory */

const INDIA_KEYWORDS = [
  "india",
  "bengaluru",
  "bangalore",
  "hyderabad",
  "chennai",
  "pune",
  "mumbai",
  "delhi",
  "noida",
  "gurgaon",
  "gurugram",
  "kochi",
  "ahmedabad",
]

const REMOTE_KEYWORDS = [
  "remote",
  "work from home",
  "wfh",
  "anywhere",
  "distributed",
]

const EUROPE_KEYWORDS = [
  "europe",
  "germany",
  "berlin",
  "austria",
  "france",
  "paris",
  "poland",
  "netherlands",
  "amsterdam",
  "uk",
  "united kingdom",
  "london",
  "spain",
  "italy",
  "switzerland",
]

const USA_KEYWORDS = [
  "usa",
  "united states",
  "u.s.",
  "us only",
  "america",
  "new york",
  "san francisco",
  "california",
  "texas",
]

const SOURCE_LABELS = {
  remoteok: "RemoteOK",
  arbeitnow: "Arbeitnow",
  linkedin: "LinkedIn",
  naukri: "Naukri",
  instahyre: "Instahyre",
  indeed: "Indeed",
}

const DEFAULT_LOCATION_FILTER = "India"
const PRIORITY_FILTER_OPTIONS = ["All", "India", "Remote"]

/**
 * @param {string} text
 */
function normalizeText(text) {
  return (text || "").toLowerCase().trim()
}

/**
 * @param {Record<string, unknown>} job
 */
export function getJobLocationText(job) {
  return [job.location, job.job_type, job.description].filter(Boolean).join(" ")
}

/**
 * @param {Record<string, unknown>} job
 */
export function isIndiaJob(job) {
  if (job.india_focused) return true
  const text = normalizeText(getJobLocationText(job))
  return INDIA_KEYWORDS.some((keyword) => text.includes(keyword))
}

/**
 * @param {Record<string, unknown>} job
 */
export function isRemoteJob(job) {
  if (job.remote_priority) return true
  const text = normalizeText(getJobLocationText(job))
  return REMOTE_KEYWORDS.some((keyword) => text.includes(keyword))
}

/**
 * @param {Record<string, unknown>} job
 */
export function isInternationalJob(job) {
  if (isIndiaJob(job) || isRemoteJob(job)) return false
  const text = normalizeText(getJobLocationText(job))
  return (
    EUROPE_KEYWORDS.some((k) => text.includes(k)) ||
    USA_KEYWORDS.some((k) => text.includes(k)) ||
    /\b(international|global|worldwide|emea|apac)\b/.test(text)
  )
}

/**
 * @param {Record<string, unknown>} job
 * @returns {LocationCategory}
 */
export function getLocationCategory(job) {
  if (isIndiaJob(job)) return "india"
  if (isRemoteJob(job)) return "remote"
  return "international"
}

/**
 * @param {Record<string, unknown>} job
 */
export function getLocationBadgeLabel(job) {
  const category = getLocationCategory(job)
  if (category === "india") return "India"
  if (category === "remote") return "Remote"
  return "International"
}

/**
 * @param {string} category
 */
export function getLocationBadgeStyle(category) {
  if (category === "india") {
    return "border-orange-500/30 bg-orange-500/10 text-orange-400"
  }
  if (category === "remote") {
    return "border-blue-500/30 bg-blue-500/10 text-blue-400"
  }
  return "border-violet-500/30 bg-violet-500/10 text-violet-400"
}

/**
 * @param {Record<string, unknown>} job
 */
export function getSourceLabel(job) {
  const key = normalizeText(String(job.source || ""))
  return SOURCE_LABELS[key] || (job.source ? String(job.source) : "Unknown")
}

/**
 * @param {string} sourceKey
 */
export function getSourceBadgeStyle(sourceKey) {
  const key = normalizeText(sourceKey)
  if (key === "remoteok") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
  }
  if (key === "arbeitnow") {
    return "border-cyan-500/30 bg-cyan-500/10 text-cyan-400"
  }
  if (key === "indeed") {
    return "border-blue-500/30 bg-blue-500/10 text-blue-400"
  }
  if (key === "naukri") {
    return "border-orange-500/30 bg-orange-500/10 text-orange-400"
  }
  if (key === "instahyre") {
    return "border-violet-500/30 bg-violet-500/10 text-violet-400"
  }
  if (key === "linkedin") {
    return "border-sky-500/30 bg-sky-500/10 text-sky-400"
  }
  return "border-border bg-muted text-muted-foreground"
}

/**
 * Extract display labels from raw location strings for dropdown + summary.
 * @param {Record<string, unknown>} job
 * @returns {string[]}
 */
export function extractLocationLabels(job) {
  const labels = new Set()
  const raw = (job.location || "").trim()

  if (!raw) {
    if (isRemoteJob(job)) labels.add("Remote")
    if (isIndiaJob(job)) labels.add("India")
    return Array.from(labels)
  }

  labels.add(raw)

  const text = normalizeText(raw)

  if (isIndiaJob(job) || INDIA_KEYWORDS.some((k) => text.includes(k))) {
    labels.add("India")
  }
  if (isRemoteJob(job) || REMOTE_KEYWORDS.some((k) => text.includes(k))) {
    labels.add("Remote")
  }
  if (EUROPE_KEYWORDS.some((k) => text.includes(k)) || text.includes("europe")) {
    labels.add("Europe")
  }
  if (text.includes("germany") || text.includes("berlin")) labels.add("Germany")
  if (text.includes("berlin")) labels.add("Berlin")
  if (USA_KEYWORDS.some((k) => text.includes(k))) labels.add("USA")

  return Array.from(labels)
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 */
export function extractLocationFilterOptions(jobs) {
  const discovered = new Set()

  for (const job of jobs) {
    extractLocationLabels(job).forEach((label) => {
      if (label && label !== "All") discovered.add(label)
    })
  }

  const dynamic = Array.from(discovered).sort((a, b) => a.localeCompare(b))

  const ordered = [...PRIORITY_FILTER_OPTIONS]
  for (const label of dynamic) {
    if (!ordered.includes(label)) ordered.push(label)
  }

  return ordered
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 * @param {string} selectedFilter
 */
export function filterJobsByLocation(jobs, selectedFilter) {
  if (!selectedFilter || selectedFilter === "All") {
    return jobs
  }

  if (selectedFilter === "India") {
    return jobs.filter(isIndiaJob)
  }

  if (selectedFilter === "Remote") {
    return jobs.filter(isRemoteJob)
  }

  const target = normalizeText(selectedFilter)

  return jobs.filter((job) => {
    const labels = extractLocationLabels(job).map((l) => normalizeText(l))
    const locationText = normalizeText(getJobLocationText(job))
    return labels.includes(target) || locationText.includes(target)
  })
}

/**
 * Build location counts for the debug summary panel.
 * @param {Array<Record<string, unknown>>} jobs
 * @returns {Array<{ label: string, count: number }>}
 */
export function buildLocationSummary(jobs) {
  const counts = new Map()

  const addCount = (label) => {
    counts.set(label, (counts.get(label) || 0) + 1)
  }

  for (const job of jobs) {
    if (isIndiaJob(job)) addCount("India")
    if (isRemoteJob(job)) addCount("Remote")
    if (isInternationalJob(job)) addCount("International")

    const raw = (job.location || "").trim()
    if (raw) addCount(raw)
  }

  return Array.from(counts.entries())
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
}

/**
 * Source counts for debug summary panel.
 * @param {Array<Record<string, unknown>>} jobs
 * @returns {Array<{ label: string, count: number }>}
 */
export function buildSourceSummary(jobs) {
  const counts = new Map()

  for (const job of jobs) {
    const label = getSourceLabel(job)
    counts.set(label, (counts.get(label) || 0) + 1)
  }

  return Array.from(counts.entries())
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
}

export { DEFAULT_LOCATION_FILTER }
