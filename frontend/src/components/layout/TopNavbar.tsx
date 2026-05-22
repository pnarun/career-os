import { Bell, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { AppPage } from "@/components/layout/Sidebar"

const pageMeta: Record<AppPage, { title: string; description: string }> = {
  dashboard: {
    title: "Dashboard",
    description: "Overview of your job search automation",
  },
  resume: {
    title: "Resume Intelligence",
    description: "Upload and analyze candidate resumes",
  },
  match: {
    title: "Job Match",
    description: "Compare resume skills against job descriptions",
  },
  jobs: {
    title: "Jobs",
    description: "Discover and match engineering roles",
  },
  settings: {
    title: "Settings",
    description: "Scheduled scans and email delivery preferences",
  },
}

type TopNavbarProps = {
  page: AppPage
}

export function TopNavbar({ page }: TopNavbarProps) {
  const meta = pageMeta[page]

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-sm">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">{meta.title}</h1>
        <p className="text-sm text-muted-foreground">{meta.description}</p>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" aria-label="Search">
          <Search className="size-4" />
        </Button>
        <Button variant="outline" size="icon" aria-label="Notifications">
          <Bell className="size-4" />
        </Button>
        <div className="ml-2 flex size-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
          U
        </div>
      </div>
    </header>
  )
}
