import { useEffect, useRef, useState } from "react"
import { ChevronDown, LogOut, User } from "lucide-react"

import { useAuth } from "@/context/AuthContext"
import { useResumeOnboarding } from "@/context/ResumeOnboardingContext"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

function initials(name, email) {
  const source = (name || email || "U").trim()
  const parts = source.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  return source.slice(0, 2).toUpperCase()
}

export function UserMenu({ onNavigate }) {
  const { user, logout } = useAuth()
  const { gateActive } = useResumeOnboarding()
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined

    const handlePointerDown = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false)
      }
    }

    const handleKeyDown = (event) => {
      if (event.key === "Escape") setOpen(false)
    }

    document.addEventListener("mousedown", handlePointerDown)
    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("mousedown", handlePointerDown)
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [open])

  if (!user) return null

  const label = initials(user.full_name, user.email)

  return (
    <div ref={menuRef} className="relative">
      <Button
        variant="outline"
        size="sm"
        className="gap-2 pl-2 pr-2"
        data-tour-id="profile-menu"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="flex size-7 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
          {label}
        </span>
        <span className="hidden max-w-[120px] truncate text-sm sm:inline">
          {user.full_name || user.email}
        </span>
        <ChevronDown className={cn("size-4 transition", open && "rotate-180")} />
      </Button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-56 rounded-lg border border-border bg-popover p-2 shadow-lg"
        >
            <div className="border-b border-border px-2 pb-2">
              <p className="truncate text-sm font-medium">{user.full_name || "User"}</p>
              <p className="truncate text-xs text-muted-foreground">{user.email}</p>
            </div>
            <div className="px-2 py-2">
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Workspace
              </p>
              <p className="text-sm">My Workspace</p>
              <p className="text-xs text-muted-foreground">Switcher coming soon</p>
            </div>
            {onNavigate ? (
              <Button
                variant="ghost"
                size="sm"
                className="mt-1 w-full justify-start gap-2"
                disabled={gateActive}
                onClick={() => {
                  if (gateActive) return
                  setOpen(false)
                  onNavigate("profile")
                }}
              >
                <User className="size-4" />
                Profile
              </Button>
            ) : null}
            <Button
              variant="ghost"
              size="sm"
              className="mt-1 w-full justify-start gap-2"
              onClick={() => {
                setOpen(false)
                logout()
              }}
            >
              <LogOut className="size-4" />
              Sign out
            </Button>
          </div>
      ) : null}
    </div>
  )
}
