import { useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  KeyRound,
  Loader2,
  Save,
  User,
} from "lucide-react"

import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import * as authService from "@/services/authService"

const TIMEZONE_OPTIONS = [
  "Asia/Kolkata",
  "Asia/Dubai",
  "Europe/Berlin",
  "Europe/London",
  "America/New_York",
  "UTC",
]

const inputClass =
  "flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"

function formatDate(iso) {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

export function Profile() {
  const { user, refreshUser } = useAuth()
  const [profileForm, setProfileForm] = useState({
    fullName: "",
    timezone: "Asia/Kolkata",
  })
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  })
  const [profileStatus, setProfileStatus] = useState("idle")
  const [passwordStatus, setPasswordStatus] = useState("idle")
  const [profileMessage, setProfileMessage] = useState(null)
  const [profileError, setProfileError] = useState(null)
  const [passwordMessage, setPasswordMessage] = useState(null)
  const [passwordError, setPasswordError] = useState(null)

  const syncFromUser = useCallback(() => {
    if (!user) return
    setProfileForm({
      fullName: user.full_name || "",
      timezone: user.timezone || "Asia/Kolkata",
    })
  }, [user])

  useEffect(() => {
    syncFromUser()
  }, [syncFromUser])

  const handleProfileSave = async (event) => {
    event.preventDefault()
    setProfileStatus("saving")
    setProfileMessage(null)
    setProfileError(null)
    try {
      await authService.updateProfile({
        fullName: profileForm.fullName.trim(),
        timezone: profileForm.timezone,
      })
      await refreshUser()
      setProfileMessage("Profile updated successfully.")
    } catch (err) {
      setProfileError(err.message || "Failed to update profile.")
    } finally {
      setProfileStatus("idle")
    }
  }

  const handlePasswordSave = async (event) => {
    event.preventDefault()
    setPasswordMessage(null)
    setPasswordError(null)

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError("New passwords do not match.")
      return
    }
    if (passwordForm.newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.")
      return
    }

    setPasswordStatus("saving")
    try {
      await authService.changePassword({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword,
      })
      setPasswordForm({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      })
      setPasswordMessage("Password updated successfully.")
    } catch (err) {
      setPasswordError(err.message || "Failed to change password.")
    } finally {
      setPasswordStatus("idle")
    }
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <User className="size-5" />
        </div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Profile</h2>
          <p className="text-sm text-muted-foreground">
            Manage your account details and security settings.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account information</CardTitle>
          <CardDescription>
            Your display name and timezone used across Career OS.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSave} className="space-y-4">
            <div>
              <label htmlFor="profile-email" className="mb-1.5 block text-sm font-medium">
                Email
              </label>
              <input
                id="profile-email"
                type="email"
                value={user.email}
                disabled
                className={`${inputClass} cursor-not-allowed opacity-60`}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Email cannot be changed from here.
              </p>
            </div>

            <div>
              <label htmlFor="profile-name" className="mb-1.5 block text-sm font-medium">
                Full name
              </label>
              <input
                id="profile-name"
                type="text"
                required
                maxLength={120}
                value={profileForm.fullName}
                onChange={(e) =>
                  setProfileForm((prev) => ({ ...prev, fullName: e.target.value }))
                }
                className={inputClass}
                placeholder="Your name"
              />
            </div>

            <div>
              <label htmlFor="profile-timezone" className="mb-1.5 block text-sm font-medium">
                Timezone
              </label>
              <select
                id="profile-timezone"
                value={profileForm.timezone}
                onChange={(e) =>
                  setProfileForm((prev) => ({ ...prev, timezone: e.target.value }))
                }
                className={inputClass}
              >
                {TIMEZONE_OPTIONS.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-3 rounded-lg border border-border bg-muted/30 p-3 text-sm sm:grid-cols-2">
              <div>
                <p className="text-xs text-muted-foreground">Member since</p>
                <p className="font-medium">{formatDate(user.created_at)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Last sign in</p>
                <p className="font-medium">{formatDate(user.last_login)}</p>
              </div>
            </div>

            {profileError ? (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="size-4 shrink-0" />
                {profileError}
              </div>
            ) : null}
            {profileMessage ? (
              <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="size-4 shrink-0" />
                {profileMessage}
              </div>
            ) : null}

            <Button type="submit" disabled={profileStatus === "saving"} className="gap-2">
              {profileStatus === "saving" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Save className="size-4" />
              )}
              Save profile
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <KeyRound className="size-4" />
            Change password
          </CardTitle>
          <CardDescription>
            Update your password to keep your account secure.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSave} className="space-y-4">
            <div>
              <label htmlFor="current-password" className="mb-1.5 block text-sm font-medium">
                Current password
              </label>
              <input
                id="current-password"
                type="password"
                required
                autoComplete="current-password"
                value={passwordForm.currentPassword}
                onChange={(e) =>
                  setPasswordForm((prev) => ({ ...prev, currentPassword: e.target.value }))
                }
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="new-password" className="mb-1.5 block text-sm font-medium">
                New password
              </label>
              <input
                id="new-password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={passwordForm.newPassword}
                onChange={(e) =>
                  setPasswordForm((prev) => ({ ...prev, newPassword: e.target.value }))
                }
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="confirm-password" className="mb-1.5 block text-sm font-medium">
                Confirm new password
              </label>
              <input
                id="confirm-password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={passwordForm.confirmPassword}
                onChange={(e) =>
                  setPasswordForm((prev) => ({ ...prev, confirmPassword: e.target.value }))
                }
                className={inputClass}
              />
            </div>

            {passwordError ? (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="size-4 shrink-0" />
                {passwordError}
              </div>
            ) : null}
            {passwordMessage ? (
              <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="size-4 shrink-0" />
                {passwordMessage}
              </div>
            ) : null}

            <Button
              type="submit"
              variant="secondary"
              disabled={passwordStatus === "saving"}
              className="gap-2"
            >
              {passwordStatus === "saving" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <KeyRound className="size-4" />
              )}
              Update password
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
