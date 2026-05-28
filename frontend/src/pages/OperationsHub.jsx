import { lazy, Suspense, useState } from "react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { PageErrorBoundary } from "@/components/PageErrorBoundary"
import { PageSectionSkeleton } from "@/components/PageSectionSkeleton"
import { useHubTabPrefetch } from "@/hooks/useHubTabPrefetch"

const Scans = lazy(() => import("@/pages/Scans").then((m) => ({ default: m.Scans })))
const Automation = lazy(() =>
  import("@/pages/Automation").then((m) => ({ default: m.Automation }))
)
const Notifications = lazy(() =>
  import("@/pages/Notifications").then((m) => ({ default: m.Notifications }))
)

const TABS = [
  { id: "scans", label: "Scans & Schedule" },
  { id: "automation", label: "Automation" },
  { id: "notifications", label: "Notifications" },
]

function readInitialTab() {
  try {
    const stored = sessionStorage.getItem("operationsHubTab")
    if (stored && TABS.some((t) => t.id === stored)) {
      sessionStorage.removeItem("operationsHubTab")
      return stored
    }
  } catch {
    /* ignore */
  }
  return "scans"
}

function TabFallback() {
  return (
    <div className="py-8">
      <PageSectionSkeleton lines={6} />
    </div>
  )
}

export function OperationsHub() {
  const [tab, setTab] = useState(readInitialTab)
  useHubTabPrefetch("operations", tab)

  return (
    <TabbedHub
      tourId="operations-hub"
      title="Scans & Automation"
      description="Run scans, connect LinkedIn with Career Lens, and manage alerts"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      <PageErrorBoundary>
        <Suspense fallback={<TabFallback />}>
          {tab === "scans" ? <Scans /> : tab === "automation" ? <Automation /> : <Notifications />}
        </Suspense>
      </PageErrorBoundary>
    </TabbedHub>
  )
}
