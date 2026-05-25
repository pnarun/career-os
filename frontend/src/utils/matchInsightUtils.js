/**
 * @param {Record<string, unknown>} job
 */
export function getMatchInsightBadges(job) {
  const badges = []
  const score = Number(job.match_percentage ?? job.match_score ?? 0)
  const recommendation = String(job.recommendation || "")

  if (recommendation) {
    badges.push({
      key: "recommendation",
      label: recommendation,
      className:
        score >= 90
          ? "bg-green-500/10 text-green-400 border-green-500/30"
          : score >= 75
            ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
            : score >= 50
              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
              : "bg-red-500/10 text-red-400 border-red-500/30",
    })
  }

  const careerFit = String(job.career_fit || "")
  if (careerFit.toLowerCase().includes("excellent")) {
    badges.push({
      key: "excellent-fit",
      label: "Excellent Match",
      className: "bg-green-500/10 text-green-400 border-green-500/30",
    })
  } else if (careerFit.toLowerCase().includes("strong")) {
    badges.push({
      key: "strong-fit",
      label: "Strong Backend Fit",
      className: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    })
  }

  if (job.remote_priority || job.job_type === "remote" || job.remote) {
    badges.push({
      key: "remote-friendly",
      label: "Remote Friendly",
      className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    })
  }

  const missing = Array.isArray(job.missing_skills) ? job.missing_skills : []
  if (missing.length === 1) {
    badges.push({
      key: "skill-gap",
      label: `Skill Gap: ${missing[0]}`,
      className: "bg-orange-500/10 text-orange-300 border-orange-500/30",
    })
  } else if (missing.length > 1) {
    badges.push({
      key: "skill-gaps",
      label: `Skill Gaps: ${missing.slice(0, 2).join(", ")}`,
      className: "bg-orange-500/10 text-orange-300 border-orange-500/30",
    })
  }

  if (score >= 80 && (job.easy_apply || job.is_easy_apply_possible)) {
    badges.push({
      key: "high-growth",
      label: "High Growth Potential",
      className: "bg-violet-500/10 text-violet-300 border-violet-500/30",
    })
  }

  return badges
}

/**
 * @param {Record<string, unknown>} job
 */
export function getStrengthSummary(job) {
  const strengths = Array.isArray(job.strengths) ? job.strengths : []
  if (strengths.length > 0) return strengths[0]
  const matched = Array.isArray(job.matched_skills) ? job.matched_skills : []
  if (matched.length > 0) {
    return `Matches ${matched.slice(0, 3).join(", ")} from your resume.`
  }
  return ""
}
