import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Briefcase,
  Calendar,
  Filter,
  Loader2,
  MessageSquare,
  Send,
  Trash2,
  TrendingUp,
} from "lucide-react"

import { ProviderIconBadge } from "@/components/ProviderIconBadge"
import { SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  APPLICATION_STATUSES,
  STATUS_TABS,
  deleteApplication,
  getApplicationAnalytics,
  getApplicationTimeline,
  getApplications,
  updateApplicationNotes,
  updateApplicationStatus,
} from "@/services/applicationService"
import { FEED_PROVIDER_OPTIONS } from "@/services/jobFeedService"
import {
  formatApplicationDate,
  getStatusBadgeStyle,
  getStatusLabel,
} from "@/utils/applicationStatusUtils"

function StatusBadge({ status }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
        getStatusBadgeStyle(status)
      )}
    >
      {getStatusLabel(status)}
    </span>
  )
}

function AnalyticsCards({ analytics }) {
  if (!analytics) return null

  const interviewRate =
    analytics.total_applied > 0
      ? Math.round((analytics.interviews / analytics.total_applied) * 100)
      : 0
  const offerRate =
    analytics.total_applied > 0
      ? Math.round((analytics.offers / analytics.total_applied) * 100)
      : 0

  const cards = [
    { label: "Jobs Saved", value: analytics.total_saved, icon: Briefcase },
    { label: "Applications Sent", value: analytics.total_applied, icon: Send },
    { label: "Interview Rate", value: `${interviewRate}%`, icon: TrendingUp },
    { label: "Offer Rate", value: `${offerRate}%`, icon: TrendingUp },
    { label: "Response Rate", value: `${analytics.response_rate}%`, icon: TrendingUp },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {cards.map(({ label, value, icon: Icon }) => (
        <Card key={label}>
          <CardContent className="flex items-center gap-3 py-4">
            <Icon className="size-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-xl font-semibold tabular-nums">{value}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function ApplicationRow({ application, onRefresh }) {
  const [notes, setNotes] = useState(application.notes || "")
  const [status, setStatus] = useState(application.status)
  const [busy, setBusy] = useState(false)
  const [timeline, setTimeline] = useState([])
  const [showTimeline, setShowTimeline] = useState(false)

  const loadTimeline = useCallback(async () => {
    const events = await getApplicationTimeline(application.application_id)
    setTimeline(events)
  }, [application.application_id])

  const onStatusChange = async (nextStatus) => {
    setBusy(true)
    try {
      const updated = await updateApplicationStatus(application.application_id, nextStatus)
      setStatus(updated.status)
      await onRefresh()
      if (showTimeline) await loadTimeline()
    } finally {
      setBusy(false)
    }
  }

  const onSaveNotes = async () => {
    setBusy(true)
    try {
      await updateApplicationNotes(application.application_id, notes)
      await onRefresh()
    } finally {
      setBusy(false)
    }
  }

  const onDelete = async () => {
    setBusy(true)
    try {
      await deleteApplication(application.application_id)
      await onRefresh()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardHeader className="space-y-2 pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <ProviderIconBadge source={application.source} />
            <CardTitle className="text-base">{application.title}</CardTitle>
            <p className="text-sm text-muted-foreground">{application.company}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <StatusBadge status={status} />
            <span className="text-xs tabular-nums text-muted-foreground">
              {application.match_score}% match
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted-foreground">
          {application.location || "Remote"}
          {application.applied_at
            ? ` · Applied ${formatApplicationDate(application.applied_at)}`
            : ` · Updated ${formatApplicationDate(application.updated_at)}`}
        </p>

        <div className="flex flex-wrap gap-2">
          <select
            value={status}
            onChange={(e) => onStatusChange(e.target.value)}
            disabled={busy}
            className="h-8 rounded-md border border-input bg-background px-2 text-xs"
          >
            {APPLICATION_STATUSES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => {
              setShowTimeline((open) => !open)
              if (!showTimeline) loadTimeline()
            }}
          >
            <Calendar className="size-3.5" />
            Timeline
          </Button>
          <Button type="button" size="sm" variant="outline" disabled={busy} onClick={onDelete}>
            <Trash2 className="size-3.5" />
            Remove
          </Button>
        </div>

        <div className="flex gap-2">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add notes…"
            rows={2}
            className="min-h-[60px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-xs"
          />
          <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={onSaveNotes}>
            <MessageSquare className="size-3.5" />
            Save
          </Button>
        </div>

        {showTimeline && timeline.length > 0 && (
          <ol className="space-y-1 border-l border-border pl-4 text-xs text-muted-foreground">
            {timeline.map((event, index) => (
              <li key={`${event.timestamp}-${event.status}-${index}`}>
                <span className="font-medium text-foreground">{getStatusLabel(event.status)}</span>
                {" · "}
                {formatApplicationDate(event.timestamp)}
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}

export function Applications() {
  const [activeTab, setActiveTab] = useState("saved")
  const [applications, setApplications] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [statusFilter, setStatusFilter] = useState("")
  const [sourceFilter, setSourceFilter] = useState("")
  const [remoteFilter, setRemoteFilter] = useState(false)
  const [minMatch, setMinMatch] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [apps, stats] = await Promise.all([
        getApplications({
          status: statusFilter || undefined,
          source: sourceFilter || undefined,
          remote: remoteFilter ? true : undefined,
          minMatch: minMatch > 0 ? minMatch : undefined,
        }),
        getApplicationAnalytics(),
      ])
      setApplications(apps)
      setAnalytics(stats)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load applications")
    } finally {
      setLoading(false)
    }
  }, [statusFilter, sourceFilter, remoteFilter, minMatch])

  useEffect(() => {
    loadData()
  }, [loadData])

  const tabConfig = STATUS_TABS.find((tab) => tab.id === activeTab) ?? STATUS_TABS[0]

  const tabApplications = useMemo(() => {
    return applications.filter((app) => tabConfig.statuses.includes(app.status))
  }, [applications, tabConfig.statuses])

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Applications</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Track saved jobs, applications, interviews, and offers in one career CRM.
        </p>
      </div>

      <AnalyticsCards analytics={analytics} />

      {analytics?.top_sources?.length > 0 && (
        <Card>
          <CardContent className="py-4 text-sm">
            <p className="mb-2 font-medium">Top job sources</p>
            <p className="text-muted-foreground">
              {analytics.top_sources.map((item) => `${item.source}: ${item.count}`).join(" · ")}
            </p>
            {analytics.top_skills?.length > 0 && (
              <>
                <p className="mb-2 mt-3 font-medium">Most common matched skills</p>
                <p className="text-muted-foreground">
                  {analytics.top_skills.map((item) => `${item.skill}: ${item.count}`).join(" · ")}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="flex flex-col gap-3 py-4 lg:flex-row lg:flex-wrap lg:items-end">
          <div className="flex flex-wrap gap-2">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-xs font-medium",
                  activeTab === tab.id
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-input text-muted-foreground"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            >
              <option value="">All statuses</option>
              {APPLICATION_STATUSES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            >
              <option value="">All providers</option>
              {FEED_PROVIDER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={0}
              max={100}
              value={minMatch}
              onChange={(e) => setMinMatch(Number(e.target.value) || 0)}
              placeholder="Min match %"
              className="h-9 w-28 rounded-md border border-input bg-background px-2 text-sm"
            />
            <label className="flex h-9 items-center gap-2 rounded-md border border-input px-3 text-sm">
              <input
                type="checkbox"
                checked={remoteFilter}
                onChange={(e) => setRemoteFilter(e.target.checked)}
              />
              Remote
            </label>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <SlowLoadingPageCenter active messageKey="page-load" className="min-h-[30vh]" />
      ) : tabApplications.length === 0 ? (
        <Card>
          <CardContent className="flex min-h-[160px] flex-col items-center justify-center gap-2 py-10 text-center">
            <Filter className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No applications in {tabConfig.label.toLowerCase()} yet. Save or mark jobs applied from
              the Jobs page.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {tabApplications.map((application) => (
            <ApplicationRow
              key={application.application_id}
              application={application}
              onRefresh={loadData}
            />
          ))}
        </div>
      )}
    </div>
  )
}
