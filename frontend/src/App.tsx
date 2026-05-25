import { lazy, Suspense, useCallback, useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

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
const InterviewPrep = lazy(() =>
  import("@/pages/InterviewPrep").then((m) => ({ default: m.InterviewPrep }))
)
const JobMatch = lazy(() => import("@/pages/JobMatch").then((m) => ({ default: m.JobMatch })))
const Jobs = lazy(() => import("@/pages/Jobs").then((m) => ({ default: m.Jobs })))
const ResumeAI = lazy(() => import("@/pages/ResumeAI").then((m) => ({ default: m.ResumeAI })))
const ResumeUpload = lazy(() =>
  import("@/pages/ResumeUpload").then((m) => ({ default: m.ResumeUpload }))
)
const Applications = lazy(() =>
  import("@/pages/Applications").then((m) => ({ default: m.Applications }))
)
const Automation = lazy(() =>
  import("@/pages/Automation").then((m) => ({ default: m.Automation }))
)
const Notifications = lazy(() =>
  import("@/pages/Notifications").then((m) => ({ default: m.Notifications }))
)
const CareerAnalytics = lazy(() =>
  import("@/pages/CareerAnalytics").then((m) => ({ default: m.CareerAnalytics }))
)
const CareerCopilot = lazy(() =>
  import("@/pages/CareerCopilot").then((m) => ({ default: m.CareerCopilot }))
)
const Scans = lazy(() => import("@/pages/Scans").then((m) => ({ default: m.Scans })))
const Settings = lazy(() => import("@/pages/Settings").then((m) => ({ default: m.Settings })))
const Profile = lazy(() => import("@/pages/Profile").then((m) => ({ default: m.Profile })))

function PageFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <Loader2 className="size-8 animate-spin text-muted-foreground" />
    </div>
  )
}

function renderPage(page: AppPage, onNavigate: (page: AppPage) => void) {
  switch (page) {
    case "dashboard":
      return <DashboardPage onNavigate={onNavigate} />
    case "resume":
      return <ResumeUpload />
    case "resume-ai":
      return <ResumeAI />
    case "interview-prep":
      return <InterviewPrep />
    case "match":
      return <JobMatch />
    case "jobs":
      return <Jobs />
    case "applications":
      return <Applications />
    case "notifications":
      return <Notifications />
    case "automation":
      return <Automation />
    case "career-analytics":
      return <CareerAnalytics />
    case "career-copilot":
      return <CareerCopilot />
    case "scans":
      return <Scans />
    case "settings":
      return <Settings />
    case "profile":
      return <Profile />
    default:
      return <DashboardPage onNavigate={onNavigate} />
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
    if (gateActive && page !== "resume") {
      setPage("resume")
    }
  }, [gateActive, page])

  return (
    <DashboardLayout activePage={page} onNavigate={handleNavigate} navLocked={gateActive}>
      <Suspense fallback={<PageFallback />}>{renderPage(page, handleNavigate)}</Suspense>
      <PlatformTour />
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
      <div className="flex min-h-svh items-center justify-center bg-background">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
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
