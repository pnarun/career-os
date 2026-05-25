import { useState, type ReactNode } from "react"

import { Sidebar, type AppPage } from "@/components/layout/Sidebar"
import { TopNavbar } from "@/components/layout/TopNavbar"
import { MobileBottomNav } from "@/components/layout/MobileBottomNav"

type DashboardLayoutProps = {
  children: ReactNode
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  navLocked?: boolean
}

export function DashboardLayout({
  children,
  activePage,
  onNavigate,
  navLocked = false,
}: DashboardLayoutProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const handleNavigate = (page: AppPage) => {
    onNavigate(page)
    setMobileNavOpen(false)
  }

  return (
    <div className="neon-app-shell relative z-0 flex h-svh overflow-hidden">
      {mobileNavOpen ? (
        <button
          type="button"
          aria-label="Close navigation menu"
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}

      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        mobileOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        navLocked={navLocked}
      />

      <div className="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden">
        <TopNavbar
          page={activePage}
          onNavigate={onNavigate}
          onMenuClick={() => setMobileNavOpen(true)}
        />
        <main className="relative z-0 flex-1 overflow-y-auto overscroll-contain p-4 pb-24 sm:p-6 lg:pb-6">
          {children}
        </main>
        <MobileBottomNav
          activePage={activePage}
          onNavigate={handleNavigate}
          navLocked={navLocked}
        />
      </div>
    </div>
  )
}
