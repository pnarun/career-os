import {
  BarChart3,
  Briefcase,
  Bot,
  Bell,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Mic,
  Radar,
  Send,
  Settings,
  Sparkles,
  Target,
  X,
} from "lucide-react"

import { cn } from "@/lib/utils"

export type AppPage =
  | "dashboard"
  | "resume"
  | "resume-ai"
  | "match"
  | "jobs"
  | "applications"
  | "notifications"
  | "automation"
  | "interview-prep"
  | "career-analytics"
  | "career-copilot"
  | "scans"
  | "settings"
  | "profile"

type NavItem = {
  id: AppPage | "applications" | "scans"
  label: string
  icon: typeof LayoutDashboard
  enabled: boolean
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, enabled: true },
  { id: "resume", label: "Resume", icon: FileText, enabled: true },
  { id: "resume-ai", label: "Resume AI", icon: Sparkles, enabled: true },
  { id: "interview-prep", label: "Interview Prep", icon: Mic, enabled: true },
  { id: "career-analytics", label: "Career Analytics", icon: BarChart3, enabled: true },
  { id: "career-copilot", label: "Career Copilot", icon: MessageSquare, enabled: true },
  { id: "match", label: "Job Match", icon: Target, enabled: true },
  { id: "jobs", label: "Jobs", icon: Briefcase, enabled: true },
  { id: "automation", label: "Automation", icon: Bot, enabled: true },
  { id: "applications", label: "Applications", icon: Send, enabled: true },
  { id: "notifications", label: "Notifications", icon: Bell, enabled: true },
  { id: "scans", label: "Scans", icon: Radar, enabled: true },
  { id: "settings", label: "Settings", icon: Settings, enabled: true },
]

const enabledPages: AppPage[] = [
  "dashboard",
  "resume",
  "resume-ai",
  "interview-prep",
  "career-analytics",
  "career-copilot",
  "match",
  "jobs",
  "applications",
  "notifications",
  "automation",
  "scans",
  "settings",
]

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  mobileOpen?: boolean
  onClose?: () => void
  navLocked?: boolean
}

export function Sidebar({
  activePage,
  onNavigate,
  mobileOpen = false,
  onClose,
  navLocked = false,
}: SidebarProps) {
  const isItemEnabled = (id: string) => {
    if (!navLocked) return true
    return id === "resume"
  }
  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex h-svh w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar/95 text-sidebar-foreground backdrop-blur-md transition-transform duration-200 ease-out lg:static lg:z-auto",
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}
    >
      <div className="flex h-16 shrink-0 items-center justify-between gap-2 border-b border-sidebar-border px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30">
            <Briefcase className="size-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight">Career OS</p>
            <p className="truncate text-xs text-muted-foreground">Job automation</p>
          </div>
        </div>
        <button
          type="button"
          aria-label="Close menu"
          className="rounded-md p-1 text-muted-foreground hover:bg-sidebar-accent/50 lg:hidden"
          onClick={onClose}
        >
          <X className="size-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto overscroll-contain p-3 sm:p-4">
        {navItems.map((item) => {
          const itemEnabled = item.enabled && isItemEnabled(item.id)
          const isActive =
            itemEnabled && enabledPages.includes(item.id as AppPage)
              ? activePage === item.id
              : false

          return (
            <button
              key={item.id}
              type="button"
              data-tour-id={item.id}
              disabled={!itemEnabled}
              onClick={() => {
                if (itemEnabled && enabledPages.includes(item.id as AppPage)) {
                  onNavigate(item.id as AppPage)
                }
              }}
              className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-500/15 text-indigo-100 shadow-[inset_0_0_0_1px_oklch(0.55_0.15_275_/_0.35)]"
                  : "text-muted-foreground",
                itemEnabled
                  ? "hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                  : "cursor-not-allowed opacity-50"
              )}
            >
              <item.icon className="size-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="shrink-0 border-t border-sidebar-border p-3 sm:p-4">
        <p className="text-xs text-muted-foreground">Job discovery ready</p>
      </div>
    </aside>
  )
}
