import { useCallback, useEffect, useState } from "react"
import {
  ArrowRight,
  BarChart3,
  Bell,
  Briefcase,
  Loader2,
  MessageSquare,
  Mic,
  MousePointerClick,
  Radar,
  RefreshCw,
  Send,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react"

import type { AppPage } from "@/components/layout/Sidebar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { getDashboardSummary, QUICK_LINKS } from "@/services/dashboardService"
import { getStatusBadgeStyle, getStatusLabel } from "@/utils/applicationStatusUtils"

type DashboardPageProps = {
  onNavigate: (page: AppPage) => void
}

const QUICK_LINK_ICONS: Partial<Record<AppPage, typeof Briefcase>> = {
  jobs: Briefcase,
  applications: Send,
  "career-analytics": BarChart3,
  "career-copilot": MessageSquare,
  "interview-prep": Mic,
  "resume-ai": Sparkles,
  automation: Radar,
  notifications: Bell,
  settings: Target,
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [data, setData] = useState<Awaited<ReturnType<typeof getDashboardSummary>> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const summary = await getDashboardSummary()
      setData(summary)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const go = (page: AppPage) => () => onNavigate(page)

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const apps = data?.applicationAnalytics
  const feed = data?.feed

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            Your job search command center — live stats and quick links
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <RefreshCw className="mr-2 size-4" />
          Refresh
        </Button>
      </div>

      {error ? (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Jobs Found"
          value={String(feed?.totalJobs ?? 0)}
          description="From your latest scan — open Jobs to browse"
          icon={Briefcase}
          onClick={go("jobs")}
        />
        <StatCard
          title="High Matches"
          value={String(feed?.highMatches ?? 0)}
          description="Roles scoring 75%+ match"
          icon={TrendingUp}
          accent="text-emerald-400"
          onClick={go("jobs")}
        />
        <StatCard
          title="Easy Apply"
          value={String(feed?.easyApply ?? 0)}
          description="One-click apply opportunities"
          icon={MousePointerClick}
          onClick={go("jobs")}
        />
        <StatCard
          title="Applications"
          value={String(apps?.total_applied ?? 0)}
          description={`${apps?.interviews ?? 0} interviews · ${apps?.offers ?? 0} offers`}
          icon={Send}
          onClick={go("applications")}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Career Growth"
          value={String(data?.growth?.career_growth_score ?? "—")}
          description={data?.growth?.primary_role ?? "Open analytics for details"}
          icon={BarChart3}
          accent="text-teal-400"
          onClick={go("career-analytics")}
        />
        <StatCard
          title="Jobs Saved"
          value={String(apps?.total_saved ?? 0)}
          description="Bookmarked in Applications CRM"
          icon={Briefcase}
          onClick={go("applications")}
        />
        <StatCard
          title="Response Rate"
          value={apps?.total_applied ? `${apps.response_rate}%` : "—"}
          description="Application response rate"
          icon={TrendingUp}
          onClick={go("applications")}
        />
        <StatCard
          title="Notifications"
          value={String(data?.unreadCount ?? 0)}
          description="Unread alerts and insights"
          icon={Bell}
          accent={data?.unreadCount ? "text-amber-400" : undefined}
          onClick={go("notifications")}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-sm">Top Matches</CardTitle>
              <CardDescription>Highest-scoring roles from your latest scan</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={go("jobs")}>
              View all
              <ArrowRight className="ml-1 size-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {feed?.topJobs?.length ? (
              <ul className="space-y-2">
                {feed.topJobs.map((job) => (
                  <li
                    key={job.id || `${job.title}-${job.company}`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/20 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{job.title}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {job.company} · {job.source}
                      </p>
                    </div>
                    <span className="shrink-0 text-sm font-semibold tabular-nums text-emerald-400">
                      {job.match_percentage}%
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border text-center">
                <p className="text-sm text-muted-foreground">No jobs yet</p>
                <Button size="sm" variant="outline" onClick={go("jobs")}>
                  Run a scan from Jobs
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Scan Status</CardTitle>
            <CardDescription>
              {feed?.scanTimestamp
                ? `Last scan: ${new Date(feed.scanTimestamp).toLocaleString()}`
                : "No scan recorded yet"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-lg border border-border bg-muted/20 px-3 py-2">
              <p className="text-xs text-muted-foreground">Status</p>
              <p className="text-lg font-semibold capitalize">{data?.scanStatus ?? "Idle"}</p>
            </div>
            {data?.scan ? (
              <ul className="space-y-1 text-xs text-muted-foreground">
                <li>{data.scan.qualified_jobs} qualified jobs</li>
                <li>{data.scan.total_fetched} fetched total</li>
                <li>Top source: {data.scan.top_source || "—"}</li>
              </ul>
            ) : null}
            <Button className="w-full" size="sm" variant="outline" onClick={go("scans")}>
              <Radar className="mr-2 size-4" />
              Automation & Scan Center
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-sm">Application Pipeline</CardTitle>
              <CardDescription>Recent activity in your CRM</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={go("applications")}>
              Open CRM
              <ArrowRight className="ml-1 size-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {data?.recentApplications?.length ? (
              <ul className="space-y-2">
                {data.recentApplications.map((app) => (
                  <li
                    key={app.id || app.application_id}
                    className="flex items-center justify-between gap-2 rounded-lg border border-border bg-muted/20 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{app.title}</p>
                      <p className="truncate text-xs text-muted-foreground">{app.company}</p>
                    </div>
                    <span
                      className={cn(
                        "shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-medium",
                        getStatusBadgeStyle(app.status)
                      )}
                    >
                      {getStatusLabel(app.status)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex min-h-[100px] flex-col items-center justify-center gap-2 text-center">
                <p className="text-sm text-muted-foreground">No applications tracked yet</p>
                <Button size="sm" variant="outline" onClick={go("jobs")}>
                  Find jobs to save
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-teal-500/20 bg-gradient-to-br from-teal-500/5 via-background to-background">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sparkles className="size-4 text-teal-400" />
              This Week
            </CardTitle>
            <CardDescription>
              {data?.weekly?.headline || data?.growth?.insights?.[0] || "Career intelligence summary"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {data?.weekly?.top_missing_skill ? (
              <p className="text-sm">
                Top skill to learn:{" "}
                <span className="font-medium text-teal-400">{data.weekly.top_missing_skill}</span>
              </p>
            ) : null}
            <ul className="space-y-1 text-sm text-muted-foreground">
              {(data?.weekly?.strongest_opportunities || data?.insights?.map((i) => i.message) || [])
                .slice(0, 3)
                .map((line) => (
                  <li key={line} className="flex items-start gap-2">
                    <Target className="mt-0.5 size-3 shrink-0 text-teal-400" />
                    {line}
                  </li>
                ))}
            </ul>
            <Button size="sm" variant="outline" onClick={go("career-analytics")}>
              Full analytics
              <ArrowRight className="ml-1 size-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Quick Links</CardTitle>
          <CardDescription>Jump to any section of Career OS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {QUICK_LINKS.map((link) => {
              const Icon = QUICK_LINK_ICONS[link.id] ?? ArrowRight
              return (
                <button
                  key={link.id}
                  type="button"
                  onClick={go(link.id as AppPage)}
                  className="flex items-start gap-3 rounded-lg border border-border bg-muted/10 p-3 text-left transition-colors hover:border-primary/40 hover:bg-muted/30"
                >
                  <Icon className={cn("mt-0.5 size-4 shrink-0", link.accent)} />
                  <div>
                    <p className="text-sm font-medium">{link.label}</p>
                    <p className="text-xs text-muted-foreground">{link.description}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
