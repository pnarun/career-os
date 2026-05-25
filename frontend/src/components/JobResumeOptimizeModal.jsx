import { useEffect, useState } from "react"
import { Loader2, Sparkles, Target, X } from "lucide-react"

import { AtsScoreGauge, KeywordHeatmap } from "@/components/resumeAi/ResumeAiCharts"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { scoreColor, tailorResumeForJob } from "@/services/resumeAiService"

export function JobResumeOptimizeModal({ job, open, onClose }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (!open || !job) {
      setResult(null)
      setError(null)
      return undefined
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    tailorResumeForJob({
      job_id: String(job.id || job.job_id || ""),
      job_description: String(job.description || ""),
      job_title: String(job.title || ""),
      job_location: String(job.location || ""),
      job_remote: Boolean(job.remote_priority),
    })
      .then((data) => {
        if (!cancelled) setResult(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Optimization failed")
        }
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
              <Sparkles className="size-5 text-indigo-400" />
              Optimize Resume for This Job
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
          <p className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-3 py-2 text-xs text-muted-foreground">
            Suggestions are based on your existing resume only — no fabricated experience.
          </p>

          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          {result && !loading && (
            <>
              <div className="flex flex-wrap items-center gap-6">
                <AtsScoreGauge score={result.ats_score_tailored} label="Tailored ATS" size={120} />
                <div className="space-y-2 text-sm">
                  <p>
                    Alignment:{" "}
                    <span className={cn("font-bold", scoreColor(result.alignment_score))}>
                      {result.alignment_score}%
                    </span>
                  </p>
                  <p className="text-muted-foreground">
                    Current ATS: {result.ats_score_before}% → Tailored: {result.ats_score_tailored}%
                  </p>
                  <p className="text-muted-foreground">
                    Projected with changes: {result.projected_ats_score}%
                  </p>
                </div>
              </div>

              {result.optimization_plan?.length > 0 && (
                <div>
                  <h3 className="mb-2 flex items-center gap-1 text-sm font-medium">
                    <Target className="size-4" />
                    Optimization Plan
                  </h3>
                  <ul className="space-y-2">
                    {result.optimization_plan.map((item, idx) => (
                      <li
                        key={idx}
                        className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm"
                      >
                        <span
                          className={cn(
                            "mr-2 rounded px-1.5 py-0.5 text-[10px] uppercase",
                            item.priority === "high"
                              ? "bg-red-500/15 text-red-300"
                              : "bg-amber-500/15 text-amber-300"
                          )}
                        >
                          {item.priority}
                        </span>
                        {item.action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.keyword_analysis && (
                <div>
                  <h3 className="mb-2 text-sm font-medium">Keyword Gaps</h3>
                  <KeywordHeatmap
                    missing={result.keyword_analysis.missing_keywords}
                    underrepresented={result.keyword_analysis.underrepresented_keywords}
                  />
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

