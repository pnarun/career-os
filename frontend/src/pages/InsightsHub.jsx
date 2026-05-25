import { useState } from "react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { CareerAnalytics } from "@/pages/CareerAnalytics"
import { CareerCopilot } from "@/pages/CareerCopilot"

const TABS = [
  { id: "analytics", label: "Analytics" },
  { id: "copilot", label: "Copilot" },
]

export function InsightsHub() {
  const [tab, setTab] = useState("analytics")

  return (
    <TabbedHub
      tourId="insights-hub"
      title="Career Intelligence"
      description="Market analytics and AI career guidance grounded in your data"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      {tab === "analytics" ? <CareerAnalytics /> : <CareerCopilot />}
    </TabbedHub>
  )
}
