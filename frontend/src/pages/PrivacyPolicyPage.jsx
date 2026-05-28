import { useCallback, useEffect, useRef, useState } from "react"
import {
  Cookie,
  Database,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Users,
} from "lucide-react"

import { CareerOsLogo } from "@/components/brand/CareerOsLogo"
import { privacyPolicyHref } from "@/lib/publicRoutes"
import { cn } from "@/lib/utils"

const LAST_UPDATED = "May 28, 2026"
/** Fixed header (h-16) + offset for in-page section targets */
const SCROLL_OFFSET_PX = 96

const ICON_ACCENTS = ["landing-icon-indigo", "landing-icon-purple", "landing-icon-orange"]
const TITLE_ACCENTS = [
  "landing-heading-indigo",
  "landing-heading-purple",
  "landing-heading-orange",
]

const SECTIONS = [
  { id: "overview", label: "Overview", icon: Sparkles },
  { id: "data-we-access", label: "Data we access", icon: Eye },
  { id: "data-we-do-not", label: "What we do not access", icon: EyeOff },
  { id: "extension-permissions", label: "Extension permissions", icon: Cookie },
  { id: "how-we-use", label: "How data is used", icon: SlidersHorizontal },
  { id: "storage", label: "Data storage", icon: Database },
  { id: "your-controls", label: "Your controls", icon: Users },
  { id: "security", label: "Security", icon: Lock },
  { id: "third-parties", label: "Third-party services", icon: Shield },
  { id: "contact", label: "Contact", icon: Mail },
]

function Section({ id, title, icon: Icon, accentIndex, children }) {
  const iconClass = ICON_ACCENTS[accentIndex % ICON_ACCENTS.length]
  const titleClass = TITLE_ACCENTS[accentIndex % TITLE_ACCENTS.length]

  return (
    <section id={id} className="scroll-mt-[6.5rem]">
      <div className="landing-card rounded-2xl p-6 sm:p-8">
        <div className="mb-4 flex items-center gap-3">
          <span
            className={cn(
              "flex size-11 shrink-0 items-center justify-center rounded-xl ring-1 ring-inset",
              iconClass
            )}
          >
            <Icon className="size-5" aria-hidden />
          </span>
          <h2 className={cn("text-xl font-semibold tracking-tight sm:text-2xl", titleClass)}>
            {title}
          </h2>
        </div>
        <div className="landing-body space-y-3 text-base leading-relaxed">{children}</div>
      </div>
    </section>
  )
}

function PolicyLink({ href, children }) {
  return (
    <a
      href={href}
      className="font-semibold text-violet-700 underline-offset-4 hover:text-orange-600 hover:underline"
    >
      {children}
    </a>
  )
}

function navLinkClass(active) {
  return cn(
    "block rounded-lg px-3 py-2 text-sm font-medium transition-colors",
    active
      ? "bg-violet-500/15 text-violet-900 shadow-[inset_0_0_0_1px_oklch(0.55_0.15_275_/_0.25)]"
      : "landing-muted hover:bg-violet-500/8 hover:text-violet-900"
  )
}

function SectionNavLink({ item, activeId, onSelect, className }) {
  return (
    <a
      href={`#${item.id}`}
      onClick={(e) => {
        e.preventDefault()
        onSelect(item.id)
      }}
      aria-current={activeId === item.id ? "true" : undefined}
      className={cn(navLinkClass(activeId === item.id), className)}
    >
      {item.label}
    </a>
  )
}

function sectionDocumentTop(el) {
  return el.getBoundingClientRect().top + window.scrollY
}

export function PrivacyPolicyPage() {
  const [activeId, setActiveId] = useState(() => {
    const hash = window.location.hash.replace("#", "")
    return SECTIONS.some((s) => s.id === hash) ? hash : SECTIONS[0].id
  })
  /** While smooth-scrolling from nav click, keep clicked section highlighted */
  const scrollLockRef = useRef(null)
  const scrollUnlockTimerRef = useRef(null)

  const resolveActiveSection = useCallback(() => {
    if (scrollLockRef.current) {
      setActiveId(scrollLockRef.current)
      return
    }

    const probe = window.scrollY + SCROLL_OFFSET_PX + 48
    let current = SECTIONS[0].id

    for (const { id } of SECTIONS) {
      const el = document.getElementById(id)
      if (!el) continue
      if (sectionDocumentTop(el) <= probe) {
        current = id
      }
    }
    setActiveId(current)
  }, [])

  const scrollToSection = useCallback(
    (id) => {
      const el = document.getElementById(id)
      if (!el) return

      scrollLockRef.current = id
      setActiveId(id)

      if (scrollUnlockTimerRef.current) {
        window.clearTimeout(scrollUnlockTimerRef.current)
      }

      const top = sectionDocumentTop(el) - SCROLL_OFFSET_PX
      window.scrollTo({ top: Math.max(0, top), behavior: "smooth" })
      window.history.replaceState(null, "", `#${id}`)

      const releaseLock = () => {
        scrollLockRef.current = null
        resolveActiveSection()
      }

      if ("onscrollend" in window) {
        const onScrollEnd = () => {
          window.removeEventListener("scrollend", onScrollEnd)
          releaseLock()
        }
        window.addEventListener("scrollend", onScrollEnd, { once: true })
        scrollUnlockTimerRef.current = window.setTimeout(releaseLock, 1200)
      } else {
        scrollUnlockTimerRef.current = window.setTimeout(releaseLock, 650)
      }
    },
    [resolveActiveSection]
  )

  useEffect(() => {
    document.documentElement.classList.add("public-scroll")
    document.title = "Privacy Policy — Career OS"
    return () => {
      document.documentElement.classList.remove("public-scroll")
    }
  }, [])

  useEffect(() => {
    const hash = window.location.hash.replace("#", "")
    if (hash && SECTIONS.some((s) => s.id === hash)) {
      requestAnimationFrame(() => scrollToSection(hash))
    }
  }, [scrollToSection])

  useEffect(() => {
    let ticking = false

    const onScroll = () => {
      if (ticking) return
      ticking = true
      requestAnimationFrame(() => {
        ticking = false
        resolveActiveSection()
      })
    }

    const onHashChange = () => {
      const id = window.location.hash.replace("#", "")
      if (SECTIONS.some((s) => s.id === id)) {
        scrollLockRef.current = id
        setActiveId(id)
        window.setTimeout(() => {
          scrollLockRef.current = null
          resolveActiveSection()
        }, 400)
      }
    }

    const scrollTargets = [
      window,
      document.documentElement,
      document.getElementById("root"),
    ].filter(Boolean)

    scrollTargets.forEach((target) => {
      target.addEventListener("scroll", onScroll, { passive: true })
    })
    window.addEventListener("hashchange", onHashChange)
    resolveActiveSection()

    return () => {
      scrollTargets.forEach((target) => {
        target.removeEventListener("scroll", onScroll)
      })
      window.removeEventListener("hashchange", onHashChange)
      if (scrollUnlockTimerRef.current) {
        window.clearTimeout(scrollUnlockTimerRef.current)
      }
    }
  }, [resolveActiveSection])

  return (
    <div className="landing-page privacy-policy-page">
      <header className="landing-header fixed inset-x-0 top-0 z-50 border-b backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <a
            href="/"
            className="flex items-center rounded-lg transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
            aria-label="Back to Career OS home"
          >
            <CareerOsLogo variant="black" size="md" className="max-h-9" />
          </a>
          <p className="landing-muted hidden text-sm font-medium sm:block">Privacy Policy</p>
        </div>
      </header>

      <div className="h-16 shrink-0" aria-hidden />

      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 sm:py-10">
        <div className="lg:grid lg:grid-cols-4 lg:items-start lg:gap-8">
          <aside className="relative hidden lg:col-span-1 lg:block">
            <nav
              className="privacy-policy-nav-fixed landing-card rounded-2xl p-2"
              aria-label="Policy sections"
            >
              <ul className="space-y-0.5">
                {SECTIONS.map((item) => (
                  <li key={item.id}>
                    <SectionNavLink
                      item={item}
                      activeId={activeId}
                      onSelect={scrollToSection}
                    />
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          <main className="min-w-0 lg:col-span-3">
            <header className="landing-section-border mb-8 border-b pb-8 sm:mb-10 sm:pb-10">
              <p className="landing-badge mb-4 inline-flex rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-wide">
                Career OS by Career Lens
              </p>
              <h1 className="landing-hero-title text-3xl font-extrabold tracking-tight sm:text-4xl">
                Privacy Policy
              </h1>
              <p className="landing-body mt-4 text-lg leading-relaxed">
                We built Career OS to help you discover and track job opportunities — not to spy on
                you. This policy explains what we access, what we never touch, and how you stay in
                control.
              </p>
              <p className="landing-muted mt-3 text-sm">Last updated: {LAST_UPDATED}</p>
            </header>

            <nav className="mb-6 lg:hidden" aria-label="Policy sections">
              <ul className="landing-card flex gap-2 overflow-x-auto rounded-2xl p-2">
                {SECTIONS.map((item) => (
                  <li key={item.id} className="shrink-0">
                    <SectionNavLink
                      item={item}
                      activeId={activeId}
                      onSelect={scrollToSection}
                      className="whitespace-nowrap"
                    />
                  </li>
                ))}
              </ul>
            </nav>

            <div className="space-y-6">
            <Section id="overview" title="Overview" icon={Sparkles} accentIndex={0}>
              <p>
                <strong className="landing-heading-indigo">Career OS</strong> is a career platform
                that helps you find roles, score matches, track applications, and run scheduled job
                scans. The <strong className="landing-heading-purple">Career Lens</strong> browser
                extension connects your LinkedIn session to Career OS so automation can run using the
                same jobs you already see when logged in to LinkedIn — without asking for your
                LinkedIn password.
              </p>
              <p>
                Automation means background scans and session sync on your behalf, based on your
                preferences. You can disconnect, stop scans, or delete sessions at any time.
              </p>
            </Section>

            <Section id="data-we-access" title="Data we access" icon={Eye} accentIndex={1}>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong>LinkedIn session cookies</strong> (via Career Lens) — only to keep your
                  LinkedIn login valid for job discovery you authorize.
                </li>
                <li>
                  <strong>Your Career OS account email</strong> — for sign-in, notifications, and
                  support.
                </li>
                <li>
                  <strong>Job preferences and settings</strong> — locations, roles, skills, scan
                  schedule, and provider choices you configure.
                </li>
                <li>
                  <strong>Scan preferences</strong> — thresholds, enabled sources, and automation
                  options you turn on.
                </li>
                <li>
                  <strong>Resume and profile data you upload</strong> — for matching, analytics, and
                  tools you use inside Career OS.
                </li>
              </ul>
            </Section>

            <Section
              id="data-we-do-not"
              title="What we do not access"
              icon={EyeOff}
              accentIndex={2}
            >
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  We do <strong>not</strong> collect or store your LinkedIn password.
                </li>
                <li>
                  We do <strong>not</strong> collect your general browsing history.
                </li>
                <li>
                  We do <strong>not</strong> record keystrokes or clipboard content.
                </li>
                <li>
                  We do <strong>not</strong> access unrelated websites — Career Lens only interacts
                  with LinkedIn and your Career OS API endpoints.
                </li>
                <li>
                  We do <strong>not</strong> read LinkedIn messages, connections lists for social
                  purposes, or private content outside job-related flows you enable.
                </li>
              </ul>
            </Section>

            <Section
              id="extension-permissions"
              title="Extension permissions"
              icon={Cookie}
              accentIndex={0}
            >
              <p>
                <strong>Cookies</strong> — Needed so Career Lens can read LinkedIn session cookies
                from your browser and send them securely to Career OS when you pair or resync. We
                never see your password; cookies are how LinkedIn already keeps you signed in.
              </p>
              <p>
                <strong>LinkedIn access</strong> — The extension only runs on LinkedIn domains to
                verify you are logged in and to sync session state. It does not run on other sites.
              </p>
              <p>
                <strong>Storage &amp; alarms</strong> — Used locally in your browser to remember
                connection status, last sync time, and to refresh sessions quietly in the
                background.
              </p>
            </Section>

            <Section id="how-we-use" title="How data is used" icon={SlidersHorizontal} accentIndex={1}>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong>Job discovery</strong> — Finding and ranking roles that match your profile.
                </li>
                <li>
                  <strong>Automation</strong> — Running scans and LinkedIn session sync you request.
                </li>
                <li>
                  <strong>Analytics</strong> — Aggregated career insights inside your account (not sold
                  to advertisers).
                </li>
                <li>
                  <strong>Notifications</strong> — Email or in-app alerts you opt into (e.g. scan
                  summaries, high-match alerts).
                </li>
              </ul>
            </Section>

            <Section id="storage" title="Data storage" icon={Database} accentIndex={2}>
              <p>
                Session and automation data are stored with access controls. LinkedIn session
                material is handled as sensitive credentials and tied to your account. Application
                data is stored in <strong>MongoDB Atlas</strong>; caching and real-time features may
                use <strong>Upstash Redis</strong>.
              </p>
              <p>
                Sessions have a lifecycle: they expire, can be refreshed via Career Lens, or removed
                when you disconnect. Stale sessions may be cleaned automatically for reliability.
              </p>
            </Section>

            <Section id="your-controls" title="Your controls" icon={Users} accentIndex={0}>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong>Disconnect LinkedIn</strong> — In Career Lens or Career OS → Scans &amp;
                  Automation.
                </li>
                <li>
                  <strong>Delete sessions</strong> — Remove stored LinkedIn automation sessions from
                  your account settings.
                </li>
                <li>
                  <strong>Revoke automation</strong> — Turn off scheduled scans and provider
                  automation.
                </li>
                <li>
                  <strong>Stop scans</strong> — Cancel or wait for in-progress scans to finish; start
                  fresh when ready.
                </li>
              </ul>
            </Section>

            <Section id="security" title="Security" icon={Lock} accentIndex={1}>
              <ul className="list-disc space-y-2 pl-5">
                <li>Passwords for Career OS are hashed; we do not store LinkedIn passwords.</li>
                <li>Traffic uses HTTPS between your browser, our API, and hosted services.</li>
                <li>Sessions are isolated per user account.</li>
                <li>
                  Internal access to production data is limited to operational needs during beta.
                </li>
              </ul>
            </Section>

            <Section id="third-parties" title="Third-party services" icon={Shield} accentIndex={2}>
              <p>Career OS relies on trusted infrastructure partners:</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong>LinkedIn</strong> — Job listings and session-based access you authorize.
                </li>
                <li>
                  <strong>Render</strong> — API hosting.
                </li>
                <li>
                  <strong>Vercel</strong> — Web application hosting.
                </li>
                <li>
                  <strong>MongoDB Atlas</strong> — Primary database.
                </li>
                <li>
                  <strong>Upstash Redis</strong> — Caching, rate limits, and real-time messaging.
                </li>
              </ul>
              <p>
                Each provider processes data according to their own policies; we only send what is
                required to operate the service.
              </p>
            </Section>

            <Section id="contact" title="Contact" icon={Mail} accentIndex={0}>
              <p>
                Questions about privacy or your data? Email us at{" "}
                <PolicyLink href="mailto:support@career-lens.in">support@career-lens.in</PolicyLink>.
              </p>
            </Section>
            </div>
          </main>
        </div>
      </div>

      <footer className="landing-section-border border-t bg-white/50 px-4 py-8 sm:px-6">
        <div className="landing-muted mx-auto max-w-6xl border-t border-violet-200/70 pt-4 text-center text-xs sm:text-sm">
          <span>
            A{" "}
            <a
              href="https://career-lens.in"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold underline-offset-4 hover:underline"
            >
              Career Lens
            </a>{" "}
            product
          </span>
          <span aria-hidden> &nbsp;•&nbsp; </span>
          <span>
            Powered by{" "}
            <a
              href="https://elvatech.in"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold underline-offset-4 hover:underline"
            >
              ELVA Tech
            </a>
          </span>
          <span aria-hidden> &nbsp;•&nbsp; </span>
          <a
            href={privacyPolicyHref()}
            className="font-semibold underline-offset-4 hover:underline"
          >
            Privacy Policy
          </a>
        </div>
      </footer>
    </div>
  )
}
