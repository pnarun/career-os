import { useCallback, useEffect, useState } from "react"
import {
  BarChart3,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Radar,
  Send,
  Settings,
  X,
} from "lucide-react"

import { CareerOsLogo } from "@/components/brand/CareerOsLogo"
import { useAuth } from "@/context/AuthContext"
import { useResumeOnboarding } from "@/context/ResumeOnboardingContext"
import { Button } from "@/components/ui/button"
import {
  markTourClosedThisSession,
  permanentlyDismissTour,
  shouldShowPlatformTour,
} from "@/lib/platformTour"
import { cn } from "@/lib/utils"

const MOBILE_MAX_WIDTH = 1023

function isMobileLayout() {
  if (typeof window === "undefined") return false
  return window.matchMedia(`(max-width: ${MOBILE_MAX_WIDTH}px)`).matches
}

const STEPS = [
  {
    id: "welcome",
    icon: LayoutDashboard,
    title: "Welcome to Career OS",
    description:
      "Your AI-powered career operating system — discover jobs, prepare for interviews, track applications, and automate your job search from one place.",
    navTarget: null,
    location: "Use the sidebar (desktop) or bottom navigation (mobile) to move between features.",
  },
  {
    id: "dashboard",
    icon: LayoutDashboard,
    title: "Dashboard",
    description:
      "Your home base with live stats, top job matches, recent scans, and quick links to the most important actions.",
    navTarget: "dashboard",
    location: "Sidebar → Dashboard",
  },
  {
    id: "resume-hub",
    icon: Briefcase,
    title: "Resume",
    description:
      "Upload and parse your resume, then switch to the Resume AI tab for ATS scoring, keyword optimization, and tailored versions.",
    navTarget: "resume-hub",
    location: "Sidebar → Resume (Upload · Resume AI tabs)",
  },
  {
    id: "jobs-hub",
    icon: Briefcase,
    title: "Jobs",
    description:
      "Browse your curated job feed from multiple providers. Use the Job Match tab to score any role against your resume.",
    navTarget: "jobs-hub",
    location: "Sidebar → Jobs (Feed · Match tabs)",
  },
  {
    id: "career-hub",
    icon: Send,
    title: "Career Track",
    description:
      "Track saved jobs, applications, and interview stages. Interview Prep provides readiness scores and mock practice.",
    navTarget: "career-hub",
    location: "Sidebar → Career Track (Applications · Interview Prep)",
  },
  {
    id: "insights-hub",
    icon: BarChart3,
    title: "Career Intelligence",
    description:
      "Market intelligence, salary insights, and growth analytics. Career Copilot is your AI assistant grounded in your data.",
    navTarget: "insights-hub",
    location: "Sidebar → Intelligence (Analytics · Copilot)",
  },
  {
    id: "operations-hub",
    icon: Radar,
    title: "Scans & Automation",
    description:
      "Run job scans, connect LinkedIn once with Career Lens, and get alerts when great matches arrive.",
    navTarget: "operations-hub",
    location: "Sidebar → Scans & Automation (Scans · Automation · Notifications)",
  },
  {
    id: "settings",
    icon: Settings,
    title: "Settings & Profile",
    description:
      "Configure job preferences, AI strictness, provider priority, and scan scheduling. Manage your account from the profile menu.",
    navTarget: "settings",
    profileTarget: "profile-menu",
    location: "Sidebar → Settings · Top-right avatar → Profile",
  },
]

function TourSpotlight({ targetId, secondaryTargetId }) {
  const [rect, setRect] = useState(null)
  const [secondaryRect, setSecondaryRect] = useState(null)

  useEffect(() => {
    if (!targetId && !secondaryTargetId) {
      setRect(null)
      setSecondaryRect(null)
      return undefined
    }

    const update = () => {
      const measure = (id) => {
        if (!id) return null
        const el = document.querySelector(`[data-tour-id="${id}"]`)
        if (!el) return null
        const box = el.getBoundingClientRect()
        return {
          top: box.top - 6,
          left: box.left - 6,
          width: box.width + 12,
          height: box.height + 12,
        }
      }
      setRect(measure(targetId))
      setSecondaryRect(measure(secondaryTargetId))
    }

    update()
    window.addEventListener("resize", update)
    window.addEventListener("scroll", update, true)
    const timer = window.setInterval(update, 300)

    return () => {
      window.removeEventListener("resize", update)
      window.removeEventListener("scroll", update, true)
      window.clearInterval(timer)
    }
  }, [targetId, secondaryTargetId])

  useEffect(() => {
    const ids = [targetId, secondaryTargetId].filter(Boolean)
    const elements = ids
      .map((id) => document.querySelector(`[data-tour-id="${id}"]`))
      .filter(Boolean)
    elements.forEach((el) => el.classList.add("platform-tour-spotlight-target"))
    return () => {
      elements.forEach((el) => el.classList.remove("platform-tour-spotlight-target"))
    }
  }, [targetId, secondaryTargetId, rect, secondaryRect])

  if (!targetId && !secondaryTargetId) {
    return (
      <div
        className="fixed inset-0 z-[190] bg-black/70 backdrop-blur-[2px]"
        aria-hidden
      />
    )
  }

  const SpotlightBox = ({ box }) =>
    box ? (
      <div
        className="pointer-events-none fixed z-[200] rounded-lg ring-2 ring-indigo-400 ring-offset-2 ring-offset-background transition-all duration-300"
        style={{
          top: box.top,
          left: box.left,
          width: box.width,
          height: box.height,
          boxShadow:
            "0 0 0 9999px oklch(0.08 0.02 270 / 0.72), 0 0 28px oklch(0.55 0.22 275 / 0.65)",
        }}
        aria-hidden
      />
    ) : null

  return (
    <>
      <SpotlightBox box={rect} />
      <SpotlightBox box={secondaryRect} />
    </>
  )
}

export function PlatformTour({ onNavigate }) {
  const { user } = useAuth()
  const { notifyTourClosed } = useResumeOnboarding()
  const [open, setOpen] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [dontShowAgain, setDontShowAgain] = useState(false)

  useEffect(() => {
    if (!user?.id || !shouldShowPlatformTour(user.id)) return

    if (isMobileLayout()) {
      markTourClosedThisSession()
      notifyTourClosed()
      return
    }

    setOpen(true)
    setStepIndex(0)
    setDontShowAgain(false)
  }, [user?.id, notifyTourClosed])

  const closeTour = useCallback(
    (permanent) => {
      if (user?.id && permanent) {
        permanentlyDismissTour(user.id)
      } else {
        markTourClosedThisSession()
      }
      setOpen(false)
      notifyTourClosed()
    },
    [user?.id, notifyTourClosed]
  )

  if (!open || !user) return null

  const step = STEPS[stepIndex]
  const StepIcon = step.icon
  const isFirst = stepIndex === 0
  const isLast = stepIndex === STEPS.length - 1
  const progress = Math.round(((stepIndex + 1) / STEPS.length) * 100)

  return (
    <>
      <TourSpotlight
        targetId={step.navTarget}
        secondaryTargetId={step.profileTarget}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="platform-tour-title"
        className="fixed inset-0 z-[210] flex items-end justify-center p-3 sm:items-center sm:p-4"
      >
        <div
          className={cn(
            "neon-glass w-full rounded-2xl p-5 shadow-2xl sm:p-6",
            "max-w-[min(100%,28rem)] sm:max-w-lg"
          )}
        >
          <div className="mb-4 flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              {step.id === "welcome" ? (
                <CareerOsLogo variant="symbol" size="sm" />
              ) : (
                <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30">
                  <StepIcon className="size-5" />
                </div>
              )}
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-indigo-300">
                  Platform tour · {stepIndex + 1} of {STEPS.length}
                </p>
                <h2 id="platform-tour-title" className="text-lg font-semibold tracking-tight">
                  {step.title}
                </h2>
              </div>
            </div>
            <button
              type="button"
              aria-label="Close tour"
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              onClick={() => closeTour(dontShowAgain)}
            >
              <X className="size-5" />
            </button>
          </div>

          <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-muted/50">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          <p className="text-sm leading-relaxed text-muted-foreground">{step.description}</p>
          <p className="mt-3 rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-3 py-2 text-xs text-indigo-200/90">
            <span className="font-medium text-indigo-200">Where: </span>
            {step.location}
          </p>

          <label className="mt-4 flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              className="size-4 rounded border-input accent-indigo-500"
            />
            Don&apos;t show again
          </label>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => closeTour(dontShowAgain)}
            >
              Skip tour
            </Button>
            <div className="flex gap-2">
              {!isFirst ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="gap-1"
                  onClick={() => setStepIndex((i) => i - 1)}
                >
                  <ChevronLeft className="size-4" />
                  Back
                </Button>
              ) : null}
              {!isLast ? (
                <Button
                  type="button"
                  size="sm"
                  className="gap-1"
                  onClick={() => {
                    const next = STEPS[stepIndex + 1]
                    if (next?.navTarget && onNavigate) {
                      onNavigate(next.navTarget)
                    }
                    setStepIndex((i) => i + 1)
                  }}
                >
                  Next
                  <ChevronRight className="size-4" />
                </Button>
              ) : (
                <Button type="button" size="sm" onClick={() => closeTour(dontShowAgain)}>
                  Get started
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
