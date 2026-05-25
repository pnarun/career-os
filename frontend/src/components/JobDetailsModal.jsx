import { useEffect, useState } from "react"
import { ExternalLink, X } from "lucide-react"

import { JobApplicationActions } from "@/components/JobApplicationActions"
import { ProviderIconBadge } from "@/components/ProviderIconBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { getSourceLabel } from "@/utils/jobLocationUtils"
import {
  canShowApplyButton,
  getApplyButtonLabel,
} from "@/utils/jobQualityUtils"
import { getMatchInsightBadges } from "@/utils/matchInsightUtils"
import {
  getApplicationTimeline,
  getApplications,
  updateApplicationNotes,
} from "@/services/applicationService"
import { formatPostedTime } from "@/utils/providerIconUtils"
import {
  formatApplicationDate,
  getStatusBadgeStyle,
  getStatusLabel,
} from "@/utils/applicationStatusUtils"

/**
 * @param {{
 *   job: Record<string, unknown> | null
 *   open: boolean
 *   onClose: () => void
 * }} props
 */
export function JobDetailsModal({ job, open, onClose }) {
  const [application, setApplication] = useState(null)
  const [notes, setNotes] = useState("")
  const [timeline, setTimeline] = useState([])
  const [savingNotes, setSavingNotes] = useState(false)

  useEffect(() => {
    if (!open || !job) return
    const jobId = String(job.id || job.job_id || "")
    getApplications({ jobId })
      .then((apps) => {
        const app = apps[0] ?? null
        setApplication(app)
        setNotes(app?.notes || "")
        if (app?.application_id) {
          return getApplicationTimeline(app.application_id).then(setTimeline)
        }
        setTimeline([])
      })
      .catch(() => {
        setApplication(null)
        setNotes("")
        setTimeline([])
      })
  }, [open, job])

  if (!open || !job) return null

  const badges = getMatchInsightBadges(job)
  const showApply = canShowApplyButton(job)
  const matched = Array.isArray(job.matched_skills) ? job.matched_skills : []
  const missing = Array.isArray(job.missing_skills) ? job.missing_skills : []
  const strengths = Array.isArray(job.strengths) ? job.strengths : []
  const recommendations = Array.isArray(job.recommendations) ? job.recommendations : []
  const whyMatch = Array.isArray(job.why_match) ? job.why_match : []
  const posted = formatPostedTime(job.posted_at || job.scan_timestamp)

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <Card
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto"
        onClick={(event) => event.stopPropagation()}
      >
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <div className="min-w-0 space-y-2">
            <ProviderIconBadge source={job.source} />
            <CardTitle className="text-lg leading-snug">{job.title}</CardTitle>
            <p className="text-sm font-medium text-foreground/80">{job.company}</p>
            <p className="text-xs text-muted-foreground">
              {job.location || "Remote"}
              {posted ? ` · Posted ${posted}` : ""}
              {" · "}
              {getSourceLabel(job)}
            </p>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X className="size-5" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-5 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-lg border px-3 py-1 text-lg font-bold tabular-nums">
              {job.match_percentage ?? job.match_score ?? 0}% match
            </span>
            {badges.map(({ key, label, className }) => (
              <span
                key={key}
                className={cn(
                  "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
                  className
                )}
              >
                {label}
              </span>
            ))}
          </div>

          {job.career_fit && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Career fit
              </p>
              <p>{job.career_fit}</p>
            </div>
          )}

          {job.experience_alignment && (
            <p className="text-muted-foreground">{job.experience_alignment}</p>
          )}

          {whyMatch.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Why this matches your profile
              </p>
              <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                {whyMatch.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {matched.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Matched skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {matched.map((skill) => (
                  <span
                    key={skill}
                    className="rounded bg-green-500/10 px-2 py-0.5 text-xs text-green-400"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {missing.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Missing skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {missing.map((skill) => (
                  <span
                    key={skill}
                    className="rounded bg-amber-500/10 px-2 py-0.5 text-xs text-amber-400"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {strengths.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Resume strengths
              </p>
              <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                {strengths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {recommendations.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Recommendations
              </p>
              <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                {recommendations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {job.description && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Job description
              </p>
              <p className="whitespace-pre-wrap text-muted-foreground">{job.description}</p>
            </div>
          )}

          <div className="space-y-3 rounded-lg border border-border p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Application tracking
            </p>
            {application && (
              <span
                className={cn(
                  "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
                  getStatusBadgeStyle(application.status)
                )}
              >
                {getStatusLabel(application.status)}
              </span>
            )}
            <JobApplicationActions job={job} compact onUpdated={setApplication} />
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Application notes…"
              rows={3}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
            />
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={savingNotes || !application?.application_id}
              onClick={async () => {
                if (!application?.application_id) return
                setSavingNotes(true)
                try {
                  const updated = await updateApplicationNotes(application.application_id, notes)
                  setApplication(updated)
                } finally {
                  setSavingNotes(false)
                }
              }}
            >
              Save notes
            </Button>
            {timeline.length > 0 && (
              <ol className="space-y-1 border-l border-border pl-4 text-xs text-muted-foreground">
                {timeline.map((event, index) => (
                  <li key={`${event.timestamp}-${index}`}>
                    <span className="font-medium text-foreground">
                      {getStatusLabel(event.status)}
                    </span>
                    {" · "}
                    {formatApplicationDate(event.timestamp)}
                  </li>
                ))}
              </ol>
            )}
          </div>

          {showApply && (
            <Button
              className="w-full"
              onClick={() => window.open(job.apply_url, "_blank", "noopener,noreferrer")}
            >
              <ExternalLink className="size-4" />
              {getApplyButtonLabel(job)}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
