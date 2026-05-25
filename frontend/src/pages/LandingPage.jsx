import {
  BarChart3,
  Bell,
  Bot,
  Briefcase,
  ChevronRight,
  MessageSquare,
  Mic,
  Radar,
  Send,
  Sparkles,
  Target,
  Zap,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const FEATURES = [
  {
    icon: Briefcase,
    title: "Curated job feed",
    accent: "purple",
    description:
      "Discover roles from LinkedIn, Indeed, Naukri, and more — matched to your skills and preferences in one place.",
  },
  {
    icon: Sparkles,
    title: "Resume AI",
    accent: "orange",
    description:
      "Upload your resume and get ATS scoring, keyword tips, and tailored versions for the roles you care about.",
  },
  {
    icon: Target,
    title: "Smart job matching",
    accent: "indigo",
    description:
      "See how well each role fits your profile with clear match scores — so you focus on opportunities worth your time.",
  },
  {
    icon: Send,
    title: "Application tracker",
    accent: "orange",
    description:
      "Save jobs, track applications, interviews, and follow-ups — never lose sight of where you stand.",
  },
  {
    icon: Mic,
    title: "Interview prep",
    accent: "purple",
    description:
      "Readiness scores, practice questions, and mock interviews so you walk in confident.",
  },
  {
    icon: BarChart3,
    title: "Career analytics",
    accent: "indigo",
    description:
      "Market trends, salary insights, and growth signals to guide your next career move.",
  },
  {
    icon: MessageSquare,
    title: "Career Copilot",
    accent: "orange",
    description:
      "An AI assistant grounded in your resume and job data — ask questions, get advice, plan your search.",
  },
  {
    icon: Radar,
    title: "Automated job scans",
    accent: "purple",
    description:
      "Schedule scans that run in the background and email you the best matches — daily or on your schedule.",
  },
  {
    icon: Bell,
    title: "Real-time alerts",
    accent: "indigo",
    description:
      "Get notified when high-match roles appear so you can apply before the crowd.",
  },
]

const STEPS = [
  {
    step: "1",
    title: "Upload your resume",
    description: "Tell us about your skills, experience, and what you're looking for.",
    stepClass: "landing-step-1",
    titleClass: "landing-heading-indigo",
  },
  {
    step: "2",
    title: "Discover & match",
    description: "We scan job boards and score roles against your profile automatically.",
    stepClass: "landing-step-2",
    titleClass: "landing-heading-orange",
  },
  {
    step: "3",
    title: "Apply & track",
    description: "Save favorites, track applications, prep for interviews, and land the role.",
    stepClass: "landing-step-3",
    titleClass: "landing-heading-purple",
  },
]

const HIGHLIGHTS = [
  { label: "Job sources", value: "5+", statClass: "landing-stat-value-0" },
  { label: "AI-powered tools", value: "Built in", statClass: "landing-stat-value-1" },
  { label: "Your data", value: "Private", statClass: "landing-stat-value-2" },
  { label: "Setup time", value: "Minutes", statClass: "landing-stat-value-3" },
]

const ICON_ACCENT = {
  purple: "landing-icon-purple",
  orange: "landing-icon-orange",
  indigo: "landing-icon-indigo",
}

const TITLE_ACCENT = {
  purple: "landing-heading-purple",
  orange: "landing-heading-orange",
  indigo: "landing-heading-indigo",
}

/** @param {{ onSignIn: () => void }} props */
export function LandingPage({ onSignIn }) {
  return (
    <div className="landing-page">
      <header className="landing-header sticky top-0 z-50 border-b backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 via-violet-600 to-orange-500 text-white shadow-md shadow-violet-500/25">
              <Briefcase className="size-4" />
            </div>
            <span className="landing-text-gradient text-lg font-bold tracking-tight">Career OS</span>
          </div>
          <Button onClick={onSignIn} size="sm" className="landing-btn-primary gap-1.5 shadow-md shadow-indigo-500/20">
            Sign in
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </header>

      <section className="relative overflow-hidden px-4 pb-16 pt-12 sm:px-6 sm:pb-24 sm:pt-20">
        <div className="relative mx-auto max-w-4xl text-center">
          <p className="landing-badge mb-4 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-wide">
            <Zap className="size-3.5 text-orange-500" />
            Your career, one platform
          </p>
          <h1 className="landing-hero-title text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
            Find, match, and land your next role
          </h1>
          <p className="landing-body mx-auto mt-6 max-w-2xl text-lg leading-relaxed sm:text-xl">
            Career OS brings{" "}
            <span className="font-semibold text-violet-700">job discovery</span>,{" "}
            <span className="font-semibold text-orange-600">resume intelligence</span>,{" "}
            <span className="font-semibold text-indigo-700">application tracking</span>, interview
            prep, and AI guidance together — so you spend less time searching and more time
            getting hired.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" className="landing-btn-primary min-w-[180px] gap-2 shadow-lg shadow-violet-500/25" onClick={onSignIn}>
              Get started free
              <ChevronRight className="size-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="landing-btn-outline min-w-[180px]"
              onClick={() => {
                document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })
              }}
            >
              See how it works
            </Button>
          </div>
        </div>

        <div className="relative mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-4 sm:grid-cols-4">
          {HIGHLIGHTS.map((item) => (
            <div key={item.label} className="landing-card landing-stat-card rounded-xl px-4 py-5 text-center">
              <p className={cn("text-2xl font-bold", item.statClass)}>{item.value}</p>
              <p className="landing-muted mt-1 text-xs font-medium">{item.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section
        id="features"
        className="landing-section-border border-t px-4 py-16 sm:px-6 sm:py-24"
      >
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="landing-heading-purple text-3xl font-bold tracking-tight sm:text-4xl">
              Everything you need to run your{" "}
              <span className="landing-heading-orange">job search</span>
            </h2>
            <p className="landing-muted mx-auto mt-4 max-w-2xl">
              No more juggling spreadsheets, tabs, and tools. Career OS is built for job seekers
              who want clarity, speed, and a real edge.
            </p>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <div key={feature.title} className="landing-card group rounded-2xl p-6 transition-all">
                <div
                  className={cn(
                    "mb-4 flex size-11 items-center justify-center rounded-xl ring-1 transition group-hover:scale-105",
                    ICON_ACCENT[feature.accent]
                  )}
                >
                  <feature.icon className="size-5" />
                </div>
                <h3 className={cn("text-lg font-bold", TITLE_ACCENT[feature.accent])}>
                  {feature.title}
                </h3>
                <p className="landing-muted mt-2 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section-border border-t bg-white/40 px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="landing-heading-indigo text-3xl font-bold tracking-tight sm:text-4xl">
              How it <span className="landing-heading-orange">works</span>
            </h2>
            <p className="landing-muted mx-auto mt-4 max-w-xl">
              Three simple steps from signup to your next opportunity.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {STEPS.map((item) => (
              <div key={item.step} className="landing-card rounded-2xl p-6 text-center md:text-left">
                <div
                  className={cn(
                    "mx-auto mb-4 flex size-12 items-center justify-center rounded-full text-lg font-bold text-white shadow-lg md:mx-0",
                    item.stepClass
                  )}
                >
                  {item.step}
                </div>
                <h3 className={cn("text-xl font-bold", item.titleClass)}>{item.title}</h3>
                <p className="landing-muted mt-2 text-sm leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section-border border-t px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-10 lg:flex-row lg:gap-16">
          <div className="flex-1">
            <div className="landing-badge mb-4 inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium">
              <Bot className="size-4 text-violet-600" />
              Set it and forget it
            </div>
            <h2 className="landing-heading-purple text-3xl font-bold tracking-tight sm:text-4xl">
              Your job search runs{" "}
              <span className="landing-heading-orange">while you sleep</span>
            </h2>
            <p className="landing-body mt-4 leading-relaxed">
              Schedule daily scans across multiple job boards. Career OS finds new roles, scores
              them against your resume, and delivers the best matches to your inbox — with live
              updates inside the app when something great appears.
            </p>
            <ul className="landing-muted mt-6 space-y-3 text-sm">
              <li className="flex items-start gap-2">
                <Radar className="mt-0.5 size-4 shrink-0 text-violet-600" />
                Automated scans on your schedule
              </li>
              <li className="flex items-start gap-2">
                <Bell className="mt-0.5 size-4 shrink-0 text-orange-500" />
                Instant alerts for high-match roles
              </li>
              <li className="flex items-start gap-2">
                <Sparkles className="mt-0.5 size-4 shrink-0 text-indigo-600" />
                AI-powered resume and interview tools included
              </li>
            </ul>
          </div>
          <div className="landing-card w-full max-w-md rounded-2xl p-8">
            <div className="space-y-4">
              {[
                { label: "Latest scan", value: "13 jobs found", valueClass: "text-violet-700" },
                { label: "Top match", value: "92% fit", valueClass: "text-orange-600" },
                { label: "Applications tracked", value: "All in one place", valueClass: "text-indigo-700" },
              ].map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between rounded-lg border border-violet-200/80 bg-white/60 px-4 py-3"
                >
                  <span className="landing-muted text-sm">{row.label}</span>
                  <span className={cn("text-sm font-semibold", row.valueClass)}>{row.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section-border border-t px-4 py-16 sm:px-6 sm:py-24">
        <div className="landing-cta-box mx-auto max-w-3xl rounded-2xl px-8 py-12 text-center">
          <h2 className="landing-heading-indigo text-3xl font-bold tracking-tight">
            Ready to take control of your{" "}
            <span className="landing-heading-orange">career</span>?
          </h2>
          <p className="landing-muted mx-auto mt-4 max-w-lg">
            Join Career OS and turn your job search into a system that works for you.
          </p>
          <Button size="lg" className="landing-btn-primary mt-8 min-w-[200px] gap-2 shadow-lg shadow-violet-500/25" onClick={onSignIn}>
            Sign in to get started
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </section>

      <footer className="landing-section-border border-t bg-white/50 px-4 py-8 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="landing-muted flex items-center gap-2 text-sm">
            <Briefcase className="size-4 text-violet-600" />
            <span>
              <span className="font-semibold text-violet-800">Career OS</span> — your AI-powered
              career platform
            </span>
          </div>
          <Button variant="ghost" size="sm" className="landing-btn-ghost" onClick={onSignIn}>
            Sign in
          </Button>
        </div>
      </footer>
    </div>
  )
}
