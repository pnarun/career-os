import { useState } from "react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { ApplicationsMapProvider } from "@/context/ApplicationsMapContext"
import { useHubTabPrefetch } from "@/hooks/useHubTabPrefetch"
import { Jobs } from "@/pages/Jobs"
import { JobMatch } from "@/pages/JobMatch"

const TABS = [
  { id: "feed", label: "Jobs Feed" },
  { id: "match", label: "Job Match" },
]

export function JobsHub() {
  const [tab, setTab] = useState("feed")
  useHubTabPrefetch("jobs", tab)

  return (
    <TabbedHub
      tourId="jobs-hub"
      title="Jobs"
      description="Browse curated matches and score any role against your resume"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      {tab === "feed" ? (
        <ApplicationsMapProvider>
          <Jobs />
        </ApplicationsMapProvider>
      ) : (
        <JobMatch />
      )}
    </TabbedHub>
  )
}
