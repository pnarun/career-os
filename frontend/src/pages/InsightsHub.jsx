import { lazy, Suspense, useState } from "react"
import { Loader2 } from "lucide-react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { PageErrorBoundary } from "@/components/PageErrorBoundary"
import { AnalyticsPageSkeleton } from "@/components/PageSectionSkeleton"
import { useHubTabPrefetch } from "@/hooks/useHubTabPrefetch"

const CareerAnalytics = lazy(() =>
  import("@/pages/CareerAnalytics").then((m) => ({ default: m.CareerAnalytics }))
)
const CareerCopilot = lazy(() =>
  import("@/pages/CareerCopilot").then((m) => ({ default: m.CareerCopilot }))
)

const TABS = [
  { id: "analytics", label: "Analytics" },
  { id: "copilot", label: "Copilot" },
]

function CopilotFallback() {
  return (
    <div className="flex min-h-[30vh] flex-col items-center justify-center gap-3 text-center">
      <Loader2 className="size-8 animate-spin text-indigo-400" />
      <p className="text-sm text-muted-foreground">Loading Copilot…</p>
    </div>
  )
}

export function InsightsHub() {
  const [tab, setTab] = useState("analytics")
  useHubTabPrefetch("insights", tab)

  return (
    <TabbedHub
      tourId="insights-hub"
      title="Career Intelligence"
      description="Market analytics and AI career guidance grounded in your data"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      <PageErrorBoundary>
        <Suspense fallback={tab === "analytics" ? <AnalyticsPageSkeleton /> : <CopilotFallback />}>
          {tab === "analytics" ? <CareerAnalytics /> : <CareerCopilot />}
        </Suspense>
      </PageErrorBoundary>
    </TabbedHub>
  )
}
