import { Menu } from "lucide-react"

import { NotificationCenter } from "@/components/NotificationCenter"
import { UserMenu } from "@/components/layout/UserMenu"
import { Button } from "@/components/ui/button"
import type { AppPage } from "@/components/layout/Sidebar"

const DEFAULT_PAGE_META = {
  title: "Career OS",
  description: "",
} as const

const pageMeta: Record<AppPage, { title: string; description: string }> = {
  dashboard: {
    title: "Dashboard",
    description: "Live stats, top matches, and quick links across Career OS",
  },
  resume: {
    title: "Resume Intelligence",
    description: "Upload and analyze the candidate resume",
  },
  "resume-ai": {
    title: "Resume AI",
    description: "ATS scoring, keyword optimization, and tailored resume intelligence",
  },
  "interview-prep": {
    title: "Interview Prep",
    description: "Readiness scoring, mock interviews, and preparation plans",
  },
  "career-analytics": {
    title: "Career Analytics",
    description: "Market intelligence, salary insights, and career growth analytics",
  },
  "career-copilot": {
    title: "Career Copilot",
    description: "AI career assistant grounded in your jobs, resume, and analytics",
  },
  match: {
    title: "Job Match",
    description: "Compare resume skills against job descriptions",
  },
  jobs: {
    title: "Jobs",
    description: "Discover and match engineering roles",
  },
  applications: {
    title: "Applications",
    description: "Track saved jobs, applications, and career progress",
  },
  notifications: {
    title: "Notifications",
    description: "Alerts, digests, reminders, and career insights",
  },
  automation: {
    title: "Automation",
    description: "Browser automation and session management",
  },
  scans: {
    title: "Automation & Scan Center",
    description: "Run scans, scheduling, history, email delivery, and provider diagnostics",
  },
  settings: {
    title: "Settings",
    description: "User, AI, notification, and provider preferences",
  },
  profile: {
    title: "Profile",
    description: "Account details, timezone, and password",
  },
}

type TopNavbarProps = {
  page: AppPage
  onNavigate?: (page: AppPage) => void
  onMenuClick?: () => void
}

export function TopNavbar({ page, onNavigate, onMenuClick }: TopNavbarProps) {
  const meta = pageMeta[page] ?? DEFAULT_PAGE_META
  const title = meta?.title ?? DEFAULT_PAGE_META.title
  const description = meta?.description ?? DEFAULT_PAGE_META.description

  return (
    <header className="relative z-30 flex h-14 shrink-0 items-center justify-between gap-3 border-b border-indigo-500/10 bg-background/75 px-4 backdrop-blur-md sm:h-16 sm:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          className="shrink-0 lg:hidden"
          aria-label="Open navigation menu"
          onClick={onMenuClick}
        >
          <Menu className="size-4" />
        </Button>
        <div className="min-w-0">
          <h1 className="truncate text-base font-semibold tracking-tight sm:text-lg">{title}</h1>
          {description ? (
            <p className="hidden truncate text-sm text-muted-foreground sm:block">{description}</p>
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        <NotificationCenter onNavigate={onNavigate} />
        <UserMenu onNavigate={onNavigate} />
      </div>
    </header>
  )
}
