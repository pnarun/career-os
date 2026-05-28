import { memo, useEffect, useState } from "react"
import {
  AlertCircle,
  BarChart3,
  Briefcase,
  Loader2,
  MapPin,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  Wallet,
} from "lucide-react"

import {
  ConversionFunnelChart,
  GrowthScoreGauge,
  LocationHeatmapChart,
  MarketTrendChart,
  ProviderRadarChart,
  SalaryBarChart,
  SkillDemandChart,
} from "@/components/careerAnalytics/CareerAnalyticsCharts"
import { EmptyState } from "@/components/EmptyState"
import { SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useCareerAnalyticsDashboard } from "@/hooks/useCareerAnalyticsDashboard"
import { cn } from "@/lib/utils"
import { humanizeErrorMessage } from "@/lib/userFacingErrors"
import { getPreferences } from "@/services/preferencesService"
import { scoreColor } from "@/services/careerAnalyticsService"

const KpiCard = memo(function KpiCard({ icon: Icon, label, value, sub }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <Icon className="size-4 shrink-0 text-muted-foreground" />
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold tabular-nums">{value}</p>
          {sub ? <p className="text-[11px] text-muted-foreground">{sub}</p> : null}
        </div>
      </CardContent>
    </Card>
  )
})

export function CareerAnalytics() {
  const [roleOptions, setRoleOptions] = useState([])
  const [selectedRole, setSelectedRole] = useState("")
  const [prefsReady, setPrefsReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    getPreferences()
      .then((prefs) => {
        if (cancelled) return
        const roles = prefs?.target_roles ?? []
        setRoleOptions(roles)
        setSelectedRole((prev) => prev || roles[0] || "")
      })
      .catch(() => {
        if (!cancelled) setSelectedRole((prev) => prev || "")
      })
      .finally(() => {
        if (!cancelled) setPrefsReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const {
    data,
    isLoading,
    isFetching,
    isPending,
    isError,
    error: queryError,
    refetch,
  } = useCareerAnalyticsDashboard(selectedRole, { enabled: prefsReady })

  const error = isError
    ? humanizeErrorMessage(
        queryError instanceof Error ? queryError.message : "Failed to load analytics"
      )
    : null

  const showLoading = !prefsReady || isPending || ((isLoading || isFetching) && !data)

  if (showLoading) {
    return (
      <SlowLoadingPageCenter
        active
        messageKey="career-analytics"
        delayMs={0}
        className="min-h-[50vh]"
      />
    )
  }

  if (isError && !data) {
    return (
      <div className="mx-auto max-w-6xl space-y-4 py-12 text-center">
        <AlertCircle className="mx-auto size-10 text-destructive" />
        <p className="text-sm font-medium text-foreground">Could not load career analytics</p>
        <p className="mx-auto max-w-md text-xs text-muted-foreground">{error}</p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 size-4" />
          Try again
        </Button>
      </div>
    )
  }

  if (!data) {
    return (
      <SlowLoadingPageCenter
        active
        messageKey="career-analytics"
        delayMs={0}
        className="min-h-[50vh]"
      />
    )
  }

  const salary = data.salary_insights
  const market = data?.market_trends
  const jobsAnalyzed = Number(market?.total_jobs_analyzed ?? 0)

  if (jobsAnalyzed === 0) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="size-6 text-teal-400" />
            <h2 className="text-2xl font-semibold tracking-tight">Career Analytics</h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Market intelligence built from your scans and job feed
          </p>
        </div>
        <EmptyState
          icon={BarChart3}
          title="Analytics will appear after your first scan"
          description="Run Fetch Jobs from the Jobs page (and connect LinkedIn via Career Lens if you use LinkedIn). Charts and salary insights need job data to analyze."
        />
      </div>
    )
  }

  const skills = data?.skill_demand
  const funnel = data?.application_funnel
  const providers = data?.provider_performance
  const growth = data?.career_growth
  const transitions = data?.role_transitions
  const heatmap = data?.market_heatmap
  const weekly = data?.weekly_insights

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="size-6 text-teal-400" />
            <h2 className="text-2xl font-semibold tracking-tight">Career Analytics</h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Market intelligence, salary insights, and career growth analytics
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {roleOptions.length > 0 && (
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="h-9 rounded-lg border border-input bg-background px-3 text-sm"
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          )}
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={cn("mr-2 size-4", isFetching && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {error && data ? (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
          Refresh failed: {error}
        </p>
      ) : null}

      {isFetching && data ? (
        <p className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="size-3.5 animate-spin" />
          Updating analytics…
        </p>
      ) : null}

      {weekly ? (
        <Card className="border-teal-500/20 bg-gradient-to-br from-teal-500/10 via-background to-background">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sparkles className="size-4 text-teal-400" />
              Weekly Insights
            </CardTitle>
            <CardDescription>{weekly.headline}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Strongest opportunities
              </p>
              <ul className="space-y-1 text-sm">
                {(weekly.strongest_opportunities || []).slice(0, 4).map((opp) => (
                  <li key={opp} className="flex items-start gap-2">
                    <Target className="mt-0.5 size-3 shrink-0 text-teal-400" />
                    {opp}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Top missing skill</p>
              <p className="text-lg font-semibold text-teal-400">{weekly.top_missing_skill}</p>
              <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
                {(weekly.summary_lines || []).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          icon={TrendingUp}
          label="Career Growth Score"
          value={data?.career_growth_score ?? 0}
          sub={growth?.primary_role}
        />
        <KpiCard icon={Wallet} label="Avg Salary" value={salary?.average_salary ?? "—"} sub={salary?.salary_range} />
        <KpiCard
          icon={Briefcase}
          label="Market Match"
          value={`${growth?.avg_market_match ?? 0}%`}
          sub={`${growth?.high_match_roles ?? 0} high-match roles`}
        />
        <KpiCard
          icon={MapPin}
          label="Remote Density"
          value={`${heatmap?.remote_opportunity_density ?? 0}%`}
          sub={(heatmap?.strongest_hiring_cities || []).slice(0, 2).join(", ")}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Career Growth Score</CardTitle>
            <CardDescription>Skill demand · market fit · applications</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4">
            <GrowthScoreGauge score={data?.career_growth_score ?? 0} />
            <ul className="w-full space-y-1 text-xs text-muted-foreground">
              {(growth?.insights || []).slice(0, 4).map((line) => (
                <li key={line} className="rounded-md bg-muted/20 px-2 py-1.5">
                  {line}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Salary Insights</CardTitle>
            <CardDescription>
              {salary?.remote_salary_premium} · {salary?.salary_growth_trend}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SalaryBarChart data={salary?.top_paying_skills} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Skill Demand</CardTitle>
            <CardDescription>Green = skills you have · Blue = market demand</CardDescription>
          </CardHeader>
          <CardContent>
            <SkillDemandChart data={skills?.demand_scores} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Skill Gap Dashboard</CardTitle>
            <CardDescription>Highest ROI skills to learn</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Strongest skills</p>
              <div className="flex flex-wrap gap-2">
                {(skills?.strongest_skills || []).map((s) => (
                  <span
                    key={s.skill}
                    className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs"
                  >
                    {s.skill} ({s.demand_pct}%)
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Missing high-value skills</p>
              <div className="flex flex-wrap gap-2">
                {(skills?.missing_high_value_skills || []).slice(0, 6).map((s) => (
                  <span
                    key={s.skill}
                    className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs"
                  >
                    {s.skill} · ROI ${(s.salary_roi_estimate / 1000).toFixed(0)}k
                  </span>
                ))}
              </div>
            </div>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {(skills?.learning_priorities || []).slice(0, 4).map((p) => (
                <li key={p.skill} className="flex items-center justify-between">
                  <span>{p.skill}</span>
                  <span className={cn("text-xs capitalize", p.priority === "high" ? "text-amber-400" : "")}>
                    {p.priority} priority
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Market Trends</CardTitle>
          <CardDescription>
            {market?.remote_market_pct}% remote · {market?.total_jobs_analyzed} jobs analyzed
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          <MarketTrendChart rising={market?.rising_technologies} declining={market?.declining_technologies} />
          <ul className="space-y-2 text-sm">
            {(market?.trend_insights || []).map((insight) => (
              <li key={insight} className="flex items-start gap-2 rounded-lg border border-border bg-muted/10 px-3 py-2">
                <TrendingUp className="mt-0.5 size-4 shrink-0 text-teal-400" />
                {insight}
              </li>
            ))}
            {(market?.fastest_growing_roles || []).slice(0, 4).map((role) => (
              <li key={role.role} className="text-xs text-muted-foreground">
                {role.role}: {role.openings} openings ({role.share_pct}%)
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Application Funnel</CardTitle>
            <CardDescription>Response rate: {funnel?.overall_response_rate ?? 0}%</CardDescription>
          </CardHeader>
          <CardContent>
            <ConversionFunnelChart funnel={funnel?.funnel} />
            <div className="mt-4 grid grid-cols-5 gap-1 text-center text-[10px]">
              {(funnel?.funnel || []).map((stage) => (
                <div key={stage.stage}>
                  <p className="font-semibold tabular-nums">{stage.count}</p>
                  <p className="text-muted-foreground">{stage.stage}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Provider Performance</CardTitle>
            <CardDescription>{providers?.best_match_provider} leads on match quality</CardDescription>
          </CardHeader>
          <CardContent>
            <ProviderRadarChart providers={providers?.providers} />
            <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
              {(providers?.summary || []).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Market Heatmap</CardTitle>
            <CardDescription>Location demand intensity</CardDescription>
          </CardHeader>
          <CardContent>
            <LocationHeatmapChart heatmap={heatmap?.heatmap} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Career Growth & Role Transitions</CardTitle>
            <CardDescription>From {transitions?.current_role}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(transitions?.suggested_transitions || []).map((t) => (
              <div
                key={t.target_role}
                className="flex items-start justify-between gap-2 rounded-lg border border-border bg-muted/10 px-3 py-2"
              >
                <div>
                  <p className="text-sm font-medium">{t.target_role}</p>
                  <p className="text-xs text-muted-foreground">{t.reason}</p>
                </div>
                <div className="text-right text-xs">
                  <p className={scoreColor(t.market_demand_score)}>{t.market_demand_score}% demand</p>
                  <p className="text-muted-foreground capitalize">{t.salary_potential} salary</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
