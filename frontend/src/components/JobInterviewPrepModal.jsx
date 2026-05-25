import { useEffect, useState } from "react"
import { Loader2, Mic, Target, X } from "lucide-react"

import { ReadinessGauge, TopicConfidenceBars } from "@/components/interviewPrep/InterviewPrepCharts"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { getInterviewPrepOverview, jobToInterviewPayload, scoreColor } from "@/services/interviewAiService"

export function JobInterviewPrepModal({ job, open, onClose }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!open || !job) {
      setData(null)
      setError(null)
      return undefined
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    getInterviewPrepOverview(jobToInterviewPayload(job))
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load prep")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [open, job])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Mic className="size-5 text-violet-400" />
              Prepare for Interview
            </h2>
            <p className="text-sm text-muted-foreground">
              {job.title} · {job.company}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </div>

        <div className="space-y-4 p-6">
          <p className="rounded-lg border border-violet-500/20 bg-violet-500/5 px-3 py-2 text-xs text-muted-foreground">
            Ethical prep only — practice before your interview, not during it.
          </p>

          {loading && (
            <div className="flex justify-center py-12">
              <Loader2 className="size-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          {data && !loading && (
            <>
              <div className="flex flex-wrap items-center gap-6">
                <ReadinessGauge score={data.readiness.readiness_score} label="Readiness" size={110} />
                <div className="space-y-1 text-sm">
                  <p>
                    Technical:{" "}
                    <span className={cn("font-bold", scoreColor(data.readiness.technical_readiness))}>
                      {data.readiness.technical_readiness}%
                    </span>
                  </p>
                  <p>
                    Behavioral:{" "}
                    <span className={cn("font-bold", scoreColor(data.readiness.behavioral_readiness))}>
                      {data.readiness.behavioral_readiness}%
                    </span>
                  </p>
                  <p className="text-muted-foreground">{data.readiness.focus_label}</p>
                </div>
              </div>

              {data.readiness.weak_areas?.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium">Weak areas</p>
                  <div className="flex flex-wrap gap-2">
                    {data.readiness.weak_areas.map((a) => (
                      <span key={a} className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <TopicConfidenceBars topics={data.readiness.topic_confidence?.slice(0, 5)} />

              <div>
                <p className="mb-2 flex items-center gap-1 text-sm font-medium">
                  <Target className="size-4" />
                  Likely questions
                </p>
                <ul className="space-y-2">
                  {[
                    ...(data.questions.technical_questions || []).slice(0, 3),
                    ...(data.questions.behavioral_questions || []).slice(0, 2),
                  ].map((q, i) => (
                    <li key={i} className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
                      {q.question}
                    </li>
                  ))}
                </ul>
              </div>

              {data.preparation_plan?.days?.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium">Preparation roadmap</p>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {data.preparation_plan.days.slice(0, 4).map((d) => (
                      <li key={d.day}>
                        Day {d.day}: {d.title}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          <Button variant="outline" className="w-full" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
