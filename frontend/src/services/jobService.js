import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

/**
 * Fetch jobs from public APIs, run match analysis, and store in MongoDB.
 * @returns {Promise<Record<string, unknown>>}
 */
/**
 * Headless LinkedIn discovery; merges new jobs into the latest scan feed.
 * @returns {Promise<Record<string, unknown>>}
 */
export async function fetchLinkedInJobs() {
  const response = await apiFetch(`/fetch-linkedin`, {
    method: "POST",
  })

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return response.json()
}

export async function fetchJobs() {
  const response = await apiFetch(`/fetch-jobs`, {
    method: "POST",
  })

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return response.json()
}

/**
 * Get all stored jobs (prioritized by match % on backend).
 * @returns {Promise<Array<Record<string, unknown>>>}
 */
export async function getJobs() {
  const response = await apiFetch(`/jobs`)

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  const jobs = await response.json()
  return sortJobsByPriority(jobs)
}

/**
 * Client-side sort mirror: match % → remote → recency.
 * @param {Array<Record<string, unknown>>} jobs
 */
export function sortJobsByPriority(jobs) {
  return [...jobs].sort((a, b) => {
    const matchDiff = (b.match_percentage ?? 0) - (a.match_percentage ?? 0)
    if (matchDiff !== 0) return matchDiff

    const remoteDiff = Number(b.remote_priority) - Number(a.remote_priority)
    if (remoteDiff !== 0) return remoteDiff

    return String(b.created_at ?? "").localeCompare(String(a.created_at ?? ""))
  })
}

/**
 * @param {string} recommendation
 * @returns {'excellent' | 'strong' | 'moderate' | 'weak' | 'default'}
 */
export function getMatchBadgeVariant(recommendation) {
  const value = (recommendation || "").toLowerCase()
  if (value.includes("excellent")) return "excellent"
  if (value.includes("strong")) return "strong"
  if (value.includes("moderate")) return "moderate"
  if (value.includes("weak")) return "weak"
  return "default"
}
