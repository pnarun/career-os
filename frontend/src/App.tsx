import { lazy, Suspense, useCallback, useEffect, useState } from "react"
import { SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"

import type { AppPage } from "@/components/layout/Sidebar"
import { useAuth } from "@/context/AuthContext"
import { ResumeOnboardingProvider, useResumeOnboarding } from "@/context/ResumeOnboardingContext"
import { DashboardLayout } from "@/layouts/DashboardLayout"
import { PlatformTour } from "@/components/PlatformTour"
import { ResumeOnboardingModal } from "@/components/ResumeOnboardingModal"
import { RealtimeToastHost } from "@/components/RealtimeToastHost"
import { PwaInstallPrompt } from "@/components/PwaInstallPrompt"
import { AuthPage } from "@/pages/AuthPage"
import { LandingPage } from "@/pages/LandingPage"

const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage }))
)
const ResumeHub = lazy(() =>
  import("@/pages/ResumeHub").then((m) => ({ default: m.ResumeHub }))
)
const JobsHub = lazy(() => import("@/pages/JobsHub").then((m) => ({ default: m.JobsHub })))
const CareerHub = lazy(() =>
  import("@/pages/CareerHub").then((m) => ({ default: m.CareerHub }))
)
const InsightsHub = lazy(() =>
  import("@/pages/InsightsHub").then((m) => ({ default: m.InsightsHub }))
)
const OperationsHub = lazy(() =>
  import("@/pages/OperationsHub").then((m) => ({ default: m.OperationsHub }))
)
const Settings = lazy(() => import("@/pages/Settings").then((m) => ({ default: m.Settings })))
const Profile = lazy(() => import("@/pages/Profile").then((m) => ({ default: m.Profile })))

function PageFallback() {
  return <SlowLoadingPageCenter active messageKey="page-load" />
}

function renderPage(page: AppPage) {
  switch (page) {
    case "dashboard":
      return <DashboardPage onNavigate={() => {}} />
    case "resume-hub":
      return <ResumeHub />
    case "jobs-hub":
      return <JobsHub />
    case "career-hub":
      return <CareerHub />
    case "insights-hub":
      return <InsightsHub />
    case "operations-hub":
      return <OperationsHub />
    case "settings":
      return <Settings />
    case "profile":
      return <Profile />
    default:
      return <DashboardPage onNavigate={() => {}} />
  }
}

function AppShell() {
  const [page, setPage] = useState<AppPage>("dashboard")
  const { gateActive, isPageAllowed } = useResumeOnboarding()

  const handleNavigate = useCallback(
    (next: AppPage) => {
      if (!isPageAllowed(next)) return
      setPage(next)
    },
    [isPageAllowed]
  )

  useEffect(() => {
    if (gateActive && page !== "resume-hub") {
      setPage("resume-hub")
    }
  }, [gateActive, page])

  return (
    <DashboardLayout activePage={page} onNavigate={handleNavigate} navLocked={gateActive}>
      <Suspense fallback={<PageFallback />}>
        {page === "dashboard" ? (
          <DashboardPage onNavigate={handleNavigate} />
        ) : (
          renderPage(page)
        )}
      </Suspense>
      <PlatformTour onNavigate={handleNavigate} />
      <ResumeOnboardingModal onNavigate={handleNavigate} />
      <RealtimeToastHost />
      <PwaInstallPrompt />
    </DashboardLayout>
  )
}

function App() {
  const { isAuthenticated, loading } = useAuth()
  const [showAuth, setShowAuth] = useState(false)

  useEffect(() => {
    if (loading || isAuthenticated) {
      document.documentElement.classList.remove("public-scroll")
      return undefined
    }
    document.documentElement.classList.add("public-scroll")
    return () => document.documentElement.classList.remove("public-scroll")
  }, [loading, isAuthenticated])

  if (loading) {
    return (
      <div className="neon-app-shell flex min-h-svh items-center justify-center bg-background">
        <SlowLoadingPageCenter active messageKey="session" />
      </div>
    )
  }

  if (isAuthenticated) {
    return (
      <ResumeOnboardingProvider>
        <AppShell />
      </ResumeOnboardingProvider>
    )
  }

  if (showAuth) {
    return <AuthPage onBack={() => setShowAuth(false)} />
  }

  return <LandingPage onSignIn={() => setShowAuth(true)} />
}

export default App
