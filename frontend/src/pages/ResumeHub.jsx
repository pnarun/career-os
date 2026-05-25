import { useState } from "react"

import { TabbedHub } from "@/components/layout/TabbedHub"
import { ResumeUpload } from "@/pages/ResumeUpload"
import { ResumeAI } from "@/pages/ResumeAI"

const TABS = [
  { id: "upload", label: "Upload Resume" },
  { id: "ai", label: "Resume AI" },
]

export function ResumeHub() {
  const [tab, setTab] = useState("upload")

  return (
    <TabbedHub
      tourId="resume-hub"
      title="Resume"
      description="Upload your resume and run ATS scoring, keywords, and tailoring"
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
    >
      {tab === "upload" ? <ResumeUpload /> : <ResumeAI />}
    </TabbedHub>
  )
}
