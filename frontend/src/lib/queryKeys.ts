/** Stable React Query keys — keep filter objects JSON-serializable. */

export const queryKeys = {
  jobs: {
    all: ["jobs"] as const,
    feed: (filters: Record<string, unknown>) => ["jobs", "feed", filters] as const,
    latestScan: () => ["jobs", "latest-scan-analytics"] as const,
  },
  dashboard: {
    core: () => ["dashboard", "core"] as const,
    insights: () => ["dashboard", "insights"] as const,
  },
  analytics: {
    career: (role: string) => ["analytics", "career", role || ""] as const,
  },
  scans: {
    center: () => ["scans", "center"] as const,
  },
  operations: {
    notifications: (tab: string) => ["operations", "notifications", tab] as const,
    automationBootstrap: () => ["operations", "automation", "bootstrap"] as const,
  },
  insights: {
    copilotOverview: () => ["insights", "copilot", "overview"] as const,
  },
  career: {
    applications: (filters: Record<string, unknown>) =>
      ["career", "applications", filters] as const,
    interviewJobs: (filter: string) => ["career", "interview-jobs", filter] as const,
  },
  resume: {
    aiOverview: (resumeId = "") => ["resume", "ai-overview", resumeId] as const,
    list: () => ["resume", "list"] as const,
  },
}
