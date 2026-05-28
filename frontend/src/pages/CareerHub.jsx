import { useState } from "react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { useHubTabPrefetch } from "@/hooks/useHubTabPrefetch"
import { Applications } from "@/pages/Applications"
import { InterviewPrep } from "@/pages/InterviewPrep"

const TABS = [
  { id: "applications", label: "Applications" },
  { id: "interview", label: "Interview Prep" },
]

export function CareerHub() {
  const [tab, setTab] = useState("applications")
  useHubTabPrefetch("career", tab)

  return (
    <TabbedHub
      tourId="career-hub"
      title="Career Track"
      description="Manage your application pipeline and interview readiness"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      {tab === "applications" ? <Applications /> : <InterviewPrep />}
    </TabbedHub>
  )
}
