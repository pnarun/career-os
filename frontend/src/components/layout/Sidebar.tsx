import {
  Briefcase,
  FileText,
  LayoutDashboard,
  Radar,
  Send,
  Settings,
  Target,
} from "lucide-react"

import { cn } from "@/lib/utils"

export type AppPage = "dashboard" | "resume" | "match" | "jobs" | "settings"

type NavItem = {
  id: AppPage | "applications" | "scans"
  label: string
  icon: typeof LayoutDashboard
  enabled: boolean
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, enabled: true },
  { id: "resume", label: "Resume", icon: FileText, enabled: true },
  { id: "match", label: "Job Match", icon: Target, enabled: true },
  { id: "jobs", label: "Jobs", icon: Briefcase, enabled: true },
  { id: "applications", label: "Applications", icon: Send, enabled: false },
  { id: "scans", label: "Scans", icon: Radar, enabled: false },
  { id: "settings", label: "Settings", icon: Settings, enabled: true },
]

const enabledPages: AppPage[] = ["dashboard", "resume", "match", "jobs", "settings"]

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-6">
        <div className="flex size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
          <Briefcase className="size-4" />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight">Career OS</p>
          <p className="text-xs text-muted-foreground">Job automation</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const isActive =
            item.enabled && enabledPages.includes(item.id as AppPage)
              ? activePage === item.id
              : false

          return (
            <button
              key={item.label}
              type="button"
              disabled={!item.enabled}
              onClick={() => {
                if (item.enabled && enabledPages.includes(item.id as AppPage)) {
                  onNavigate(item.id as AppPage)
                }
              }}
              className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-muted-foreground",
                item.enabled
                  ? "hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                  : "cursor-not-allowed opacity-50"
              )}
            >
              <item.icon className="size-4 shrink-0" />
              {item.label}
            </button>
          )
        })}
      </nav>
      <div className="border-t border-sidebar-border p-4">
        <p className="text-xs text-muted-foreground">Job discovery ready</p>
      </div>
    </aside>
  )
}
