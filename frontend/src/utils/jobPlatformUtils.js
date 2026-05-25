import { getSourceLabel } from "@/utils/jobLocationUtils"
import { filterJobsByLocation } from "@/utils/jobLocationUtils"
import { KNOWN_PROVIDERS } from "@/utils/providerStatusUtils"

export const DEFAULT_PLATFORM_FILTER = "All"

const PLATFORM_PRIORITY_OPTIONS = ["All", ...KNOWN_PROVIDERS]

/**
 * @param {Record<string, unknown>} job
 */
export function normalizeJobSourceKey(job) {
  return String(job.source || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "")
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 */
export function extractPlatformFilterOptions(jobs) {
  const discovered = new Set()

  for (const job of jobs) {
    const key = normalizeJobSourceKey(job)
    if (key) discovered.add(key)
  }

  const dynamic = Array.from(discovered).sort((a, b) => a.localeCompare(b))
  const ordered = [...PLATFORM_PRIORITY_OPTIONS]

  for (const key of dynamic) {
    if (!ordered.includes(key)) ordered.push(key)
  }

  return ordered.map((key) => ({
    value: key === "All" ? "All" : key,
    label: key === "All" ? "All" : getSourceLabel({ source: key }),
  }))
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 * @param {string} selectedFilter
 */
export function filterJobsByPlatform(jobs, selectedFilter) {
  if (!selectedFilter || selectedFilter === "All") {
    return jobs
  }

  const target = selectedFilter.toLowerCase()
  return jobs.filter((job) => normalizeJobSourceKey(job) === target)
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 * @param {string[]} selectedProviders
 */
export function filterJobsByProviders(jobs, selectedProviders) {
  if (!selectedProviders?.length) return jobs
  const allowed = new Set(
    selectedProviders.map((p) => p.trim().toLowerCase().replace(/\s+/g, ""))
  )
  return jobs.filter((job) => allowed.has(normalizeJobSourceKey(job)))
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 * @param {string} locationFilter
 * @param {string} platformFilter
 */
export function filterJobsByLocationAndPlatform(
  jobs,
  locationFilter,
  platformFilter
) {
  return filterJobsByPlatform(
    filterJobsByLocation(jobs, locationFilter),
    platformFilter
  )
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 * @param {string} locationFilter
 * @param {string[]} selectedProviders
 */
export function filterJobsByLocationAndProviders(
  jobs,
  locationFilter,
  selectedProviders
) {
  return filterJobsByProviders(
    filterJobsByLocation(jobs, locationFilter),
    selectedProviders
  )
}

export { KNOWN_PROVIDERS }
