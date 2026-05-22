/**
 * Job quality scoring display and apply-button safety checks.
 */

const QUALITY_SCORE_STYLES = {
  high: "bg-green-500/15 text-green-400 border-green-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-red-500/15 text-red-400 border-red-500/30",
  default: "bg-muted text-muted-foreground border-border",
}

const BADGE_STYLES = {
  verified: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  remote: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  india: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  easyApply: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  suspicious: "bg-red-500/15 text-red-400 border-red-500/30",
  quality: "bg-muted text-muted-foreground border-border",
}

/**
 * @param {Record<string, unknown>} job
 */
export function getJobQualityScore(job) {
  return Number(job?.job_quality_score ?? 0)
}

/**
 * @param {number} score
 */
export function getQualityScoreStyle(score) {
  if (score >= 70) return QUALITY_SCORE_STYLES.high
  if (score >= 40) return QUALITY_SCORE_STYLES.medium
  return QUALITY_SCORE_STYLES.low
}

/**
 * @param {Record<string, unknown>} job
 */
export function isJobSuspicious(job) {
  return Boolean(job?.is_suspicious)
}

/**
 * @param {Record<string, unknown>} job
 */
export function canShowApplyButton(job) {
  if (isJobSuspicious(job)) return false
  if (!job?.has_apply_url) return false
  const url = String(job?.apply_url || "").trim()
  return url.length > 0 && /^https?:\/\//i.test(url)
}

/**
 * @param {Record<string, unknown>} job
 */
export function getApplyButtonLabel(job) {
  return job?.is_easy_apply_possible ? "Easy Apply" : "Apply"
}

/**
 * @param {Record<string, unknown>} job
 * @returns {Array<{ key: string, label: string, className: string }>}
 */
export function getQualityBadges(job) {
  const badges = []
  const flags = Array.isArray(job?.quality_flags) ? job.quality_flags : []
  const score = getJobQualityScore(job)

  if (isJobSuspicious(job)) {
    badges.push({ key: "suspicious", label: "Suspicious", className: BADGE_STYLES.suspicious })
  } else if (flags.includes("verified") || score >= 70) {
    badges.push({ key: "verified", label: "Verified", className: BADGE_STYLES.verified })
  }

  if (job?.remote_priority) {
    badges.push({ key: "remote", label: "Remote", className: BADGE_STYLES.remote })
  }

  if (job?.india_focused) {
    badges.push({ key: "india", label: "India", className: BADGE_STYLES.india })
  }

  if (job?.is_easy_apply_possible) {
    badges.push({
      key: "easy-apply",
      label: "Easy Apply",
      className: BADGE_STYLES.easyApply,
    })
  }

  if (score > 0) {
    badges.push({
      key: "quality-score",
      label: `Q${score}`,
      className: getQualityScoreStyle(score),
    })
  }

  return badges
}

/**
 * Human-readable rejection insight from quality flags (debug).
 * @param {Record<string, unknown>} job
 */
export function getQualityRejectionInsight(job) {
  if (!isJobSuspicious(job) && getJobQualityScore(job) >= 30) {
    return null
  }

  const flags = Array.isArray(job?.quality_flags) ? job.quality_flags : []
  const reasons = []

  if (isJobSuspicious(job)) reasons.push("suspicious")
  if (getJobQualityScore(job) < 30) reasons.push("low_quality_score")
  if (flags.includes("suspicious_job")) reasons.push("failed_validation")
  if (!job?.has_apply_url) reasons.push("invalid_apply_url")

  return reasons.length > 0 ? reasons.join(", ") : "quality_gate"
}

/**
 * @param {Array<Record<string, unknown>>} jobs
 */
export function buildQualityDebugSummary(jobs) {
  if (!jobs?.length) {
    return {
      avgQualityScore: 0,
      suspiciousCount: 0,
      verifiedCount: 0,
      withApplyUrlCount: 0,
    }
  }

  let scoreSum = 0
  let suspiciousCount = 0
  let verifiedCount = 0
  let withApplyUrlCount = 0

  for (const job of jobs) {
    scoreSum += getJobQualityScore(job)
    if (isJobSuspicious(job)) suspiciousCount += 1
    if (job?.has_apply_url) withApplyUrlCount += 1
    const flags = Array.isArray(job?.quality_flags) ? job.quality_flags : []
    if (flags.includes("verified") || (!job?.is_suspicious && getJobQualityScore(job) >= 70)) {
      verifiedCount += 1
    }
  }

  return {
    avgQualityScore: Math.round(scoreSum / jobs.length),
    suspiciousCount,
    verifiedCount,
    withApplyUrlCount,
  }
}

export { BADGE_STYLES, QUALITY_SCORE_STYLES }
