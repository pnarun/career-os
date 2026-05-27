import {
  BarChart3,
  Briefcase,
  FileText,
  LayoutDashboard,
  Radar,
  Send,
  Settings,
  X,
} from "lucide-react"

import { cn } from "@/lib/utils"

export type AppPage =
  | "dashboard"
  | "resume-hub"
  | "jobs-hub"
  | "career-hub"
  | "insights-hub"
  | "operations-hub"
  | "settings"
  | "profile"

type NavItem = {
  id: AppPage
  label: string
  icon: typeof LayoutDashboard
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "resume-hub", label: "Resume", icon: FileText },
  { id: "jobs-hub", label: "Jobs", icon: Briefcase },
  { id: "career-hub", label: "Career Track", icon: Send },
  { id: "insights-hub", label: "Intelligence", icon: BarChart3 },
  { id: "operations-hub", label: "Scans & Automation", icon: Radar },
  { id: "settings", label: "Settings", icon: Settings },
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
  const isItemEnabled = (id: AppPage) => {
    if (!navLocked) return true
    return id === "resume-hub"
  }

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex h-svh w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar/95 text-sidebar-foreground backdrop-blur-md transition-transform duration-200 ease-out lg:static lg:z-auto",
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}
    >
      <div className="flex h-16 shrink-0 items-center justify-between gap-2 border-b border-sidebar-border px-4 sm:px-6">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-2 rounded-lg text-left transition-colors hover:bg-sidebar-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
          onClick={() => onNavigate("dashboard")}
          aria-label="Go to dashboard"
        >
          <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30">
            <Briefcase className="size-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight">Career OS</p>
            <p className="truncate text-xs text-muted-foreground">Find, match & land roles</p>
          </div>
        </button>
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
          const itemEnabled = isItemEnabled(item.id)
          const isActive = itemEnabled && activePage === item.id

          return (
            <button
              key={item.id}
              type="button"
              data-tour-id={item.id}
              disabled={!itemEnabled}
              onClick={() => {
                if (itemEnabled) onNavigate(item.id)
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

    </aside>
  )
}
