import { useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  Target,
  XCircle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { SlowLoadingFormHint } from "@/components/SlowLoadingStatus"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { matchJob } from "@/services/matchService"

function TagList({ items, variant = "default", emptyLabel }) {
  if (!items?.length) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className={cn(
            "rounded-md px-2.5 py-1 text-xs font-medium",
            variant === "matched" && "bg-green-500/15 text-green-400",
            variant === "missing" && "bg-amber-500/15 text-amber-400",
            variant === "default" && "bg-muted text-foreground"
          )}
        >
          {item}
        </span>
      ))}
    </div>
  )
}

function scoreColor(percentage) {
  if (percentage >= 90) return "text-green-400"
  if (percentage >= 75) return "text-emerald-400"
  if (percentage >= 50) return "text-amber-400"
  return "text-red-400"
}

export function JobMatch() {
  const [jobDescription, setJobDescription] = useState("")
  const [resumeId, setResumeId] = useState("")
  const [useLatestResume, setUseLatestResume] = useState(true)
  const [status, setStatus] = useState("idle")
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const isLoading = status === "loading"

  const onSubmit = async () => {
    setError(null)
    setResult(null)
    setStatus("loading")

    try {
      const data = await matchJob({
        resumeId: useLatestResume ? "" : resumeId,
        jobDescription,
      })
      setResult(data)
      setStatus("success")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Match analysis failed.")
      setStatus("error")
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Job Match</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Compare your resume skills against a job description.
        </p>
      </div>

      {/* Job Description Input */}
      <Card>
        <CardHeader>
          <CardTitle>Job description</CardTitle>
          <CardDescription>Paste the full job posting or required skills section</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste job description here…"
            rows={10}
            className="w-full resize-y rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />

          <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useLatestResume}
                onChange={(e) => setUseLatestResume(e.target.checked)}
                className="size-4 rounded border-border"
              />
              Use latest uploaded resume
            </label>

            {!useLatestResume && (
              <div>
                <label
                  htmlFor="resume-id"
                  className="mb-1 block text-xs font-medium text-muted-foreground"
                >
                  Resume ID
                </label>
                <input
                  id="resume-id"
                  type="text"
                  value={resumeId}
                  onChange={(e) => setResumeId(e.target.value)}
                  placeholder="MongoDB resume ObjectId"
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 font-mono text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
            )}
          </div>

          <SlowLoadingFormHint active={isLoading} messageKey="job-match" />
          <Button onClick={onSubmit} disabled={isLoading || !jobDescription.trim()}>
            {isLoading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Analyzing match…
              </>
            ) : (
              <>
                <Target className="size-4" />
                Run match analysis
              </>
            )}
          </Button>

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          {/* Match Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Match analysis</CardTitle>
              <CardDescription>
                Resume {result.resume_id ? `· ${result.resume_id}` : ""}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-6 sm:flex-row sm:items-center">
              <div className="flex size-28 shrink-0 flex-col items-center justify-center rounded-xl border border-border bg-muted/30">
                <span
                  className={cn(
                    "text-3xl font-bold tabular-nums",
                    scoreColor(result.match_percentage)
                  )}
                >
                  {result.match_percentage}%
                </span>
                <span className="text-xs text-muted-foreground">match</span>
              </div>
              <div className="space-y-2">
                <p className="flex items-center gap-2 text-lg font-semibold">
                  <Sparkles className="size-5 text-primary" />
                  {result.recommendation}
                </p>
                <p className="text-sm text-muted-foreground">
                  {result.matched_skills?.length ?? 0} of{" "}
                  {result.job_skills?.length ?? 0} required job skills found on your
                  resume.
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle2 className="size-4 text-green-500" />
                  Matched skills
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TagList
                  items={result.matched_skills}
                  variant="matched"
                  emptyLabel="No matching skills found"
                />
              </CardContent>
            </Card>

            {/* Missing Skills */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <XCircle className="size-4 text-amber-500" />
                  Missing skills
                </CardTitle>
                <CardDescription>Required by JD but not detected on resume</CardDescription>
              </CardHeader>
              <CardContent>
                <TagList
                  items={result.missing_skills}
                  variant="missing"
                  emptyLabel="No missing skills — great coverage"
                />
              </CardContent>
            </Card>
          </div>

          {/* Match Recommendation + JD skills */}
          <Card>
            <CardHeader>
              <CardTitle>Match recommendation</CardTitle>
              <CardDescription>Based on skill overlap with the job description</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm leading-relaxed text-foreground">
                {result.match_percentage >= 90 &&
                  "Your resume strongly aligns with this role. Prioritize applying and tailoring bullets to highlight matched skills."}
                {result.match_percentage >= 75 &&
                  result.match_percentage < 90 &&
                  "This is a strong fit. Address missing skills in your summary or consider upskilling on the gaps listed above."}
                {result.match_percentage >= 50 &&
                  result.match_percentage < 75 &&
                  "Moderate alignment. Emphasize matched skills in your application and be prepared to speak to missing areas."}
                {result.match_percentage < 50 &&
                  "Limited skill overlap detected. Review missing skills before applying or target roles closer to your profile."}
              </p>
              <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  Skills detected in job description
                </p>
                <TagList
                  items={result.job_skills}
                  emptyLabel="No skills detected in job description"
                />
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
