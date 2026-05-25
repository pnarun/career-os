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

export function OperationsHub() {
  const [tab, setTab] = useState("scans")

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
