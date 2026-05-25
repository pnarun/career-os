import { BarChart3, Briefcase, Home, Radar, FileText } from "lucide-react"

import type { AppPage } from "@/components/layout/Sidebar"
import { cn } from "@/lib/utils"

const items: { id: AppPage; label: string; icon: typeof Home }[] = [
  { id: "dashboard", label: "Home", icon: Home },
  { id: "resume-hub", label: "Resume", icon: FileText },
  { id: "jobs-hub", label: "Jobs", icon: Briefcase },
  { id: "operations-hub", label: "Scans", icon: Radar },
  { id: "insights-hub", label: "Intel", icon: BarChart3 },
]

type MobileBottomNavProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  navLocked?: boolean
}

export function MobileBottomNav({
  activePage,
  onNavigate,
  navLocked = false,
}: MobileBottomNavProps) {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-indigo-500/15 bg-background/85 backdrop-blur-md lg:hidden"
      aria-label="Mobile navigation"
    >
      <div className="mx-auto flex max-w-lg items-stretch justify-around px-1 pb-[env(safe-area-inset-bottom)]">
        {items.map((item) => {
          const active = activePage === item.id
          const enabled = !navLocked || item.id === "resume-hub"
          return (
            <button
              key={item.id}
              type="button"
              data-tour-id={item.id}
              disabled={!enabled}
              onClick={() => {
                if (enabled) onNavigate(item.id)
              }}
              className={cn(
                "flex min-w-0 flex-1 flex-col items-center gap-0.5 px-1 py-2.5 text-[10px] font-medium transition-colors",
                active ? "text-indigo-300" : "text-muted-foreground",
                !enabled && "cursor-not-allowed opacity-50"
              )}
            >
              <item.icon className={cn("size-5", active && "stroke-[2.5]")} />
              <span className="truncate">{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
