import { useState } from "react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { Automation } from "@/pages/Automation"
import { Notifications } from "@/pages/Notifications"
import { Scans } from "@/pages/Scans"

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

export function OperationsHub() {
  const [tab, setTab] = useState(readInitialTab)

  return (
    <TabbedHub
      tourId="operations-hub"
      title="Scans & Automation"
      description="Scheduled job discovery, browser sessions, and alerts"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      {tab === "scans" ? <Scans /> : tab === "automation" ? <Automation /> : <Notifications />}
    </TabbedHub>
  )
}
