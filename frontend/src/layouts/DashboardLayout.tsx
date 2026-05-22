import type { ReactNode } from "react"

import { Sidebar, type AppPage } from "@/components/layout/Sidebar"
import { TopNavbar } from "@/components/layout/TopNavbar"

type DashboardLayoutProps = {
  children: ReactNode
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

export function DashboardLayout({
  children,
  activePage,
  onNavigate,
}: DashboardLayoutProps) {
  return (
    <div className="flex min-h-svh bg-background">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavbar page={activePage} />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
