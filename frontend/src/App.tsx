import { useState } from "react"

import type { AppPage } from "@/components/layout/Sidebar"
import { DashboardLayout } from "@/layouts/DashboardLayout"
import { DashboardPage } from "@/pages/DashboardPage"
import { JobMatch } from "@/pages/JobMatch"
import { Jobs } from "@/pages/Jobs"
import { ResumeUpload } from "@/pages/ResumeUpload"
import { Settings } from "@/pages/Settings"

function renderPage(page: AppPage) {
  switch (page) {
    case "dashboard":
      return <DashboardPage />
    case "resume":
      return <ResumeUpload />
    case "match":
      return <JobMatch />
    case "jobs":
      return <Jobs />
    case "settings":
      return <Settings />
    default:
      return <DashboardPage />
  }
}

function App() {
  const [page, setPage] = useState<AppPage>("dashboard")

  return (
    <DashboardLayout activePage={page} onNavigate={setPage}>
      {renderPage(page)}
    </DashboardLayout>
  )
}

export default App
