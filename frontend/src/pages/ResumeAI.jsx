import {
  AlertCircle,
  ArrowUpRight,
  Download,
  Loader2,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import {
  AtsScoreGauge,
  FactorBar,
  KeywordHeatmap,
  SkillRadarChart,
} from "@/components/resumeAi/ResumeAiCharts"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  downloadExportResult,
  exportResume,
  getResumeAiOverview,
  scoreColor,
} from "@/services/resumeAiService"

function SectionCard({ title, description, children, className }) {
  return (
    <Card className={cn("border-border/80", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}

export function ResumeAI() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [exporting, setExporting] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const overview = await getResumeAiOverview()
      setData(overview)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load Resume AI")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const onExport = async (format) => {
    if (!data?.resume_id) return
    setExporting(format)
    try {
      const result = await exportResume({ resume_id: data.resume_id, format })
      downloadExportResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed")
    } finally {
      setExporting(null)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="mx-auto max-w-lg space-y-4 p-8 text-center">
        <AlertCircle className="mx-auto size-10 text-amber-400" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={load}>Retry</Button>
      </div>
    )
  }

  const { ats, feedback, keywords, skill_gaps, variants } = data

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Sparkles className="size-6 text-indigo-400" />
            Resume AI
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            ATS intelligence & truthful optimization for{" "}
            <span className="font-medium text-foreground">{data.resume_filename}</span>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {["txt", "docx", "pdf"].map((fmt) => (
            <Button
              key={fmt}
              variant="outline"
              size="sm"
              disabled={!!exporting}
              onClick={() => onExport(fmt)}
            >
              {exporting === fmt ? (
                <Loader2 className="mr-1 size-3 animate-spin" />
              ) : (
                <Download className="mr-1 size-3" />
              )}
              {fmt.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-4 py-3 text-sm text-muted-foreground">
        All recommendations are based on your existing resume. Career OS never fabricates
        experience — only suggests truthful improvements.
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard title="ATS Score" description="Overall ATS compatibility">
          <div className="relative mx-auto flex justify-center py-4">
            <AtsScoreGauge score={ats.ats_score} />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-center text-sm">
            {[
              ["Keywords", ats.keyword_score],
              ["Format", ats.format_score],
              ["Skills", ats.skills_score],
              ["Experience", ats.experience_score],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-muted-foreground">{label}</p>
                <p className={cn("font-semibold", scoreColor(value))}>{value}%</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Score Factors"
          description="What drives your ATS score"
          className="lg:col-span-2"
        >
          <div className="space-y-3">
            {Object.entries(ats.factors || {}).map(([key, value]) => (
              <FactorBar
                key={key}
                label={key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                value={value}
              />
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <SectionCard title="Strengths" description="What's working well">
          <ul className="space-y-2 text-sm">
            {feedback.strengths?.map((item) => (
              <li key={item} className="flex gap-2 text-emerald-300/90">
                <TrendingUp className="mt-0.5 size-4 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
        <SectionCard title="High-Impact Changes" description="Prioritized improvements">
          <ul className="space-y-2 text-sm">
            {feedback.high_impact_changes?.map((item) => (
              <li key={item} className="flex gap-2 text-amber-200/90">
                <ArrowUpRight className="mt-0.5 size-4 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>

      {feedback.weaknesses?.length > 0 && (
        <SectionCard title="Areas to Improve">
          <ul className="grid gap-2 sm:grid-cols-2">
            {feedback.weaknesses.map((item) => (
              <li key={item} className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard
          title="Keyword Optimization"
          description={`${keywords.coverage_percent}% coverage vs market demand`}
        >
          <KeywordHeatmap
            missing={keywords.missing_keywords}
            underrepresented={keywords.underrepresented_keywords}
          />
        </SectionCard>

        <SectionCard title="Skill Gap Analysis" description={skill_gaps.strongest_area}>
          <SkillRadarChart data={skill_gaps.skill_radar} />
          <p className="mt-3 text-sm text-muted-foreground">
            Growth focus:{" "}
            <span className="text-foreground">{skill_gaps.growth_recommendation}</span>
          </p>
          {skill_gaps.top_missing_skills?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {skill_gaps.top_missing_skills.slice(0, 6).map((gap) => (
                <span
                  key={gap.skill}
                  className="rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1 text-xs"
                >
                  {gap.skill}
                </span>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard
        title="Resume Variants"
        description={`Recommended: ${variants.recommended_variant?.replace("_", " ")}`}
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {variants.variants?.map((variant) => (
            <div
              key={variant.variant_id}
              className={cn(
                "rounded-lg border p-4",
                variant.variant_id === variants.recommended_variant
                  ? "border-indigo-500/40 bg-indigo-500/10"
                  : "border-border"
              )}
            >
              <div className="flex items-center justify-between">
                <p className="font-medium">{variant.label}</p>
                <span className={cn("text-sm font-bold", scoreColor(variant.match_score))}>
                  {variant.match_score}%
                </span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">{variant.summary_hint}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {variant.focus_skills?.slice(0, 4).map((s) => (
                  <span key={s} className="rounded bg-muted px-1.5 py-0.5 text-[10px]">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  )
}
