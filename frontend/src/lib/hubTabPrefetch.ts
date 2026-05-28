import type { QueryClient } from "@tanstack/react-query"

import { DEFAULT_JOBS_FEED_FILTERS } from "@/lib/defaultJobsFeedFilters"
import { queryKeys } from "@/lib/queryKeys"
import { logPrefetch } from "@/lib/prefetchDiagnostics"
import { STALE_TIMES } from "@/lib/staleTimes"
import { DEFAULT_APPLICATIONS_FILTERS } from "@/hooks/useApplicationsCenter"
import {
  getAutomationAnalytics,
  getCareerInsights,
  getNotifications,
} from "@/services/notificationService"
import {
  getLinkedInAutomationStatus,
  getSessionStatus,
} from "@/services/automationService"
import { getApplicationAnalytics, getApplications } from "@/services/applicationService"
import { getCopilotHistory, getCopilotOverview } from "@/services/copilotService"
import { getInterviewPrepJobs } from "@/services/interviewAiService"
import { getJobsFeed } from "@/services/jobFeedService"
import { getResumeAiOverview } from "@/services/resumeAiService"
import { listResumes } from "@/services/preferencesService"
import { loadScanCenterData } from "@/services/scansService"

const PREFETCH_DELAY_MS = 500
const PREFETCH_STAGGER_MS = 280

export type HubId = "operations" | "insights" | "jobs" | "career" | "resume"

const HUB_TAB_PREFETCH: Record<HubId, Record<string, Array<(qc: QueryClient) => Promise<void>>>> = {
  operations: {
    scans: [
      (qc) => prefetchScanCenter(qc),
      (qc) => prefetchAutomationBootstrap(qc),
      (qc) => prefetchNotifications(qc, "all"),
    ],
    automation: [
      (qc) => prefetchScanCenter(qc),
      (qc) => prefetchNotifications(qc, "all"),
    ],
    notifications: [
      (qc) => prefetchScanCenter(qc),
      (qc) => prefetchAutomationBootstrap(qc),
    ],
  },
  insights: {
    analytics: [(qc) => prefetchCopilotOverview(qc)],
    copilot: [],
  },
  jobs: {
    feed: [(qc) => prefetchJobsFeedDefault(qc)],
    match: [(qc) => prefetchJobsFeedDefault(qc)],
  },
  career: {
    applications: [(qc) => prefetchInterviewPrepJobs(qc, "all")],
    interview: [(qc) => prefetchApplicationsCenter(qc)],
  },
  resume: {
    upload: [
      (qc) => prefetchResumeAiOverview(qc),
      (qc) => prefetchResumeList(qc),
    ],
    ai: [(qc) => prefetchResumeList(qc)],
  },
}

async function prefetchIfNeeded(
  qc: QueryClient,
  queryKey: readonly unknown[],
  queryFn: () => Promise<unknown>,
  staleTime: number
) {
  const state = qc.getQueryState(queryKey)
  if (state?.dataUpdatedAt && Date.now() - state.dataUpdatedAt < staleTime) {
    logPrefetch("PREFETCH_SKIPPED_CACHE_HIT", queryKey)
    return
  }
  if (state?.fetchStatus === "fetching") {
    logPrefetch("PREFETCH_SKIPPED_CACHE_HIT", queryKey, "in-flight")
    return
  }

  logPrefetch("PREFETCH_STARTED", queryKey)
  await qc.prefetchQuery({ queryKey, queryFn, staleTime })
  logPrefetch("PREFETCH_COMPLETED", queryKey)
}

export async function prefetchScanCenter(qc: QueryClient) {
  const queryKey = queryKeys.scans.center()
  await prefetchIfNeeded(qc, queryKey, loadScanCenterData, STALE_TIMES.scanCenter)
}

export async function prefetchAutomationBootstrap(qc: QueryClient) {
  const queryKey = queryKeys.operations.automationBootstrap()
  await prefetchIfNeeded(
    qc,
    queryKey,
    async () => {
      const [sessionRes, linkedinRes] = await Promise.all([
        getSessionStatus(),
        getLinkedInAutomationStatus(),
      ])
      return {
        sessions: sessionRes.sessions ?? {},
        linkedin: linkedinRes,
      }
    },
    STALE_TIMES.scanCenter
  )
}

export async function prefetchNotifications(qc: QueryClient, tab = "all") {
  const queryKey = queryKeys.operations.notifications(tab)
  await prefetchIfNeeded(
    qc,
    queryKey,
    async () => {
      const typeFilter = tab === "all" ? undefined : tab
      const [notifData, insightData, analyticsData] = await Promise.all([
        getNotifications({ type: typeFilter, limit: 100 }),
        getCareerInsights(10),
        getAutomationAnalytics(5),
      ])
      return {
        notifications: notifData.notifications ?? [],
        insights: insightData ?? [],
        analytics: analyticsData,
      }
    },
    STALE_TIMES.scanCenter
  )
}

export async function prefetchCopilotOverview(qc: QueryClient) {
  const queryKey = queryKeys.insights.copilotOverview()
  await prefetchIfNeeded(
    qc,
    queryKey,
    async () => {
      const ov = await getCopilotOverview()
      const hist = await getCopilotHistory(10).catch(() => ({ history: [] }))
      return { overview: ov, history: hist.history ?? [] }
    },
    STALE_TIMES.dashboardInsights
  )
}

export async function prefetchJobsFeedDefault(qc: QueryClient) {
  const f = DEFAULT_JOBS_FEED_FILTERS
  const queryKey = queryKeys.jobs.feed(f)
  await prefetchIfNeeded(
    qc,
    queryKey,
    () =>
      getJobsFeed({
        providers: f.providers,
        remoteOnly: f.remoteOnly,
        easyApplyOnly: f.easyApplyOnly,
        sort: f.sort,
        strongMatchesOnly: f.strongMatchesOnly,
        remoteHighMatch: f.remoteHighMatch,
        easyApplyHighMatch: f.easyApplyHighMatch,
        company: f.company || undefined,
      }),
    STALE_TIMES.jobsFeed
  )
}

export async function prefetchApplicationsCenter(qc: QueryClient) {
  const f = DEFAULT_APPLICATIONS_FILTERS
  const queryKey = queryKeys.career.applications(f)
  await prefetchIfNeeded(
    qc,
    queryKey,
    async () => {
      const [applications, analytics] = await Promise.all([
        getApplications({
          status: undefined,
          source: undefined,
          remote: undefined,
          minMatch: undefined,
        }),
        getApplicationAnalytics(),
      ])
      return { applications, analytics }
    },
    STALE_TIMES.scanCenter
  )
}

export async function prefetchInterviewPrepJobs(qc: QueryClient, filter = "all") {
  const queryKey = queryKeys.career.interviewJobs(filter)
  await prefetchIfNeeded(
    qc,
    queryKey,
    async () => {
      const result = await getInterviewPrepJobs(filter)
      return result.jobs ?? []
    },
    STALE_TIMES.scanCenter
  )
}

export async function prefetchResumeAiOverview(qc: QueryClient) {
  const queryKey = queryKeys.resume.aiOverview("")
  await prefetchIfNeeded(
    qc,
    queryKey,
    () => getResumeAiOverview(),
    STALE_TIMES.dashboardInsights
  )
}

export async function prefetchResumeList(qc: QueryClient) {
  const queryKey = queryKeys.resume.list()
  await prefetchIfNeeded(qc, queryKey, listResumes, STALE_TIMES.scanCenter)
}

function scheduleIdle(task: () => void, delayMs: number) {
  const run = () => {
    if (typeof requestIdleCallback === "function") {
      requestIdleCallback(() => task(), { timeout: 2500 })
    } else {
      task()
    }
  }
  window.setTimeout(run, delayMs)
}

/**
 * After hub mount, stagger-prefetch sibling tab queries (non-blocking).
 */
export function scheduleHubTabPrefetch(
  qc: QueryClient,
  hub: HubId,
  activeTab: string
) {
  const tasks = HUB_TAB_PREFETCH[hub]?.[activeTab] ?? []
  if (!tasks.length) return

  scheduleIdle(() => {
    tasks.forEach((task, index) => {
      window.setTimeout(() => {
        void task(qc).catch(() => {})
      }, index * PREFETCH_STAGGER_MS)
    })
  }, PREFETCH_DELAY_MS)
}
