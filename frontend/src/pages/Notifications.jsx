import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import {
  Bell,
  Briefcase,
  CheckCheck,
  Loader2,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from "lucide-react"

import { SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { useNotificationsCenter } from "@/hooks/useNotificationsCenter"
import { queryKeys } from "@/lib/queryKeys"
import {
  generateCareerInsights,
  markAllNotificationsRead,
  markNotificationRead,
  NOTIFICATION_TABS,
  NOTIFICATION_TYPES,
} from "@/services/notificationService"

function formatRelativeTime(iso) {
  if (!iso) return ""
  const date = new Date(iso)
  const diffMs = Date.now() - date.getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return "Just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function AnalyticsCards({ analytics }) {
  if (!analytics) return null
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Scans Completed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{analytics.scans_completed ?? 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Jobs Analyzed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{analytics.jobs_analyzed ?? 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Notifications Sent
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{analytics.notifications_sent ?? 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            High Matches Found
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{analytics.high_matches_found ?? 0}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export function Notifications() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState("all")
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState(null)

  const { data, isLoading, isFetching, error: fetchError, refetch } =
    useNotificationsCenter(activeTab)
  const notifications = data?.notifications ?? []
  const insights = data?.insights ?? []
  const analytics = data?.analytics ?? null
  const loading = isLoading && !data
  const queryError =
    fetchError instanceof Error
      ? fetchError.message
      : fetchError
        ? "Failed to load notifications"
        : null
  const error = queryError || generateError

  const loadData = () => {
    void refetch()
  }

  const handleMarkRead = async (id) => {
    await markNotificationRead(id)
    queryClient.setQueryData(queryKeys.operations.notifications(activeTab), (prev) => {
      if (!prev) return prev
      return {
        ...prev,
        notifications: prev.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
      }
    })
  }

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead()
    queryClient.setQueryData(queryKeys.operations.notifications(activeTab), (prev) => {
      if (!prev) return prev
      return {
        ...prev,
        notifications: prev.notifications.map((n) => ({ ...n, read: true })),
      }
    })
  }

  const handleGenerateInsights = async () => {
    setGenerating(true)
    setGenerateError(null)
    try {
      const result = await generateCareerInsights()
      queryClient.setQueryData(queryKeys.operations.notifications(activeTab), (prev) => {
        if (!prev) return prev
        return { ...prev, insights: result.insights ?? [] }
      })
    } catch (err) {
      setGenerateError(
        err instanceof Error ? err.message : "Failed to generate insights"
      )
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-sm text-muted-foreground">
            High-match alerts, digests, reminders, and career insights
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading || isFetching}>
            <RefreshCw className={cn("mr-2 size-4", (loading || isFetching) && "animate-spin")} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            <CheckCheck className="mr-2 size-4" />
            Mark all read
          </Button>
        </div>
      </div>

      <AnalyticsCards analytics={analytics} />

      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {NOTIFICATION_TABS.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Bell className="size-4" />
                Notification Feed
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <SlowLoadingPageCenter active messageKey="notifications" className="min-h-[200px]" />
              ) : notifications.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  No notifications in this category yet.
                </p>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={cn(
                        "rounded-lg border border-border p-4 transition-colors",
                        !notification.read && "border-primary/30 bg-primary/5"
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{notification.title}</p>
                            {notification.priority === "high" && (
                              <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
                                Priority
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {notification.message}
                          </p>
                          <p className="mt-2 text-xs text-muted-foreground">
                            {NOTIFICATION_TYPES[notification.type] ?? notification.type}
                            {" · "}
                            {formatRelativeTime(notification.created_at)}
                          </p>
                        </div>
                        {!notification.read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="shrink-0 text-xs"
                            onClick={() => handleMarkRead(notification.id)}
                          >
                            Mark read
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="size-4" />
                Career Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={handleGenerateInsights}
                disabled={generating}
              >
                {generating ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : (
                  <TrendingUp className="mr-2 size-4" />
                )}
                Generate insights
              </Button>
              {insights.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Run a scan and generate insights to see career guidance.
                </p>
              ) : (
                insights.slice(0, 6).map((insight) => (
                  <div
                    key={insight.id}
                    className="rounded-md border border-border p-3 text-sm"
                  >
                    <p className="font-medium">{insight.title}</p>
                    <p className="mt-1 text-muted-foreground">{insight.message}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {analytics?.provider_performance && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Briefcase className="size-4" />
                  Provider Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {Object.entries(analytics.provider_performance).map(
                    ([source, count]) => (
                      <li
                        key={source}
                        className="flex items-center justify-between"
                      >
                        <span className="capitalize">{source}</span>
                        <span className="font-medium">{count} scans</span>
                      </li>
                    )
                  )}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
