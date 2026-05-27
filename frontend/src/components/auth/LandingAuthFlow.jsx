import { useState } from "react"
import { ArrowLeft, Briefcase, Loader2 } from "lucide-react"

import { useAuth } from "@/context/AuthContext"
import { SlowLoadingFormHint } from "@/components/SlowLoadingStatus"
import { WakeAwareButton } from "@/components/WakeAwareButton"
import { AppModal } from "@/components/ui/AppModal"
import { Button } from "@/components/ui/button"
import { PasswordInput } from "@/components/ui/PasswordInput"
import { useBackendWake } from "@/context/BackendWakeContext"
import { cn } from "@/lib/utils"
import * as authApi from "@/services/authService"

const landingInputClass =
  "flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400"

const authInputClass =
  "flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm"

function detectTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Kolkata"
  } catch {
    return "Asia/Kolkata"
  }
}

function AuthBrand({ dark }) {
  return (
    <div className="mb-4 flex flex-col items-center text-center">
      <div
        className={cn(
          "mb-3 flex size-12 items-center justify-center rounded-xl text-white shadow-lg",
          dark
            ? "neon-glow-sm bg-gradient-to-br from-indigo-500 to-violet-600"
            : "bg-gradient-to-br from-indigo-600 via-violet-600 to-orange-500 shadow-violet-500/30"
        )}
      >
        <Briefcase className="size-6" />
      </div>
    </div>
  )
}

/**
 * Centered auth modals over the landing page (email → password / register).
 */
export function LandingAuthFlow({ open, onClose }) {
  const { login, register } = useAuth()
  const { ready, waking, failed, retryWake } = useBackendWake()
  const [step, setStep] = useState("email")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [otp, setOtp] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [otpSent, setOtpSent] = useState(false)
  const [devOtpHint, setDevOtpHint] = useState("")
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [busyAction, setBusyAction] = useState(null)

  const isCredentialsStep = step !== "email"
  const backdrop = isCredentialsStep ? "dark" : "light"
  const panelVariant = isCredentialsStep ? "auth" : "landing"

  const handleClose = () => {
    if (busy) return
    setStep("email")
    setPassword("")
    setFullName("")
    setDisplayName("")
    setOtp("")
    setNewPassword("")
    setOtpSent(false)
    setDevOtpHint("")
    setError(null)
    setMessage(null)
    onClose?.()
  }

  const resetAlerts = () => {
    setError(null)
    setMessage(null)
  }

  const goEmail = () => {
    setStep("email")
    setPassword("")
    setOtp("")
    setNewPassword("")
    setOtpSent(false)
    setDevOtpHint("")
    setDisplayName("")
    resetAlerts()
  }

  const onEmailContinue = async (e) => {
    e.preventDefault()
    setBusyAction("check-email")
    setBusy(true)
    resetAlerts()
    try {
      const result = await authApi.checkEmail(email.trim())
      const name = String(result.full_name || "").trim()
      setDisplayName(name)
      setStep(result.exists ? "login" : "onboarding")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not verify email")
    } finally {
      setBusy(false)
      setBusyAction(null)
    }
  }

  const onLogin = async (e) => {
    e.preventDefault()
    setBusyAction("login")
    setBusy(true)
    resetAlerts()
    try {
      await login({ email: email.trim(), password })
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed")
    } finally {
      setBusy(false)
      setBusyAction(null)
    }
  }

  const onOnboarding = async (e) => {
    e.preventDefault()
    setBusyAction("register")
    setBusy(true)
    resetAlerts()
    try {
      if (password.length < 8) {
        throw new Error("Password must be at least 8 characters.")
      }
      await register({
        email: email.trim(),
        password,
        fullName: fullName.trim(),
        timezone: detectTimezone(),
      })
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account")
    } finally {
      setBusy(false)
      setBusyAction(null)
    }
  }

  const startForgot = async () => {
    setStep("forgot")
    setOtp("")
    setNewPassword("")
    setOtpSent(false)
    setDevOtpHint("")
    resetAlerts()
    setBusyAction("reset-send")
    setBusy(true)
    try {
      const result = await authApi.requestPasswordReset(email.trim())
      setOtpSent(true)
      setMessage(result.message || "Verification code sent.")
      if (result.dev_otp) setDevOtpHint(result.dev_otp)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send code")
    } finally {
      setBusy(false)
      setBusyAction(null)
    }
  }

  const resendOtp = async () => {
    setBusyAction("reset-send")
    setBusy(true)
    resetAlerts()
    try {
      const result = await authApi.requestPasswordReset(email.trim())
      setMessage("New code sent.")
      if (result.dev_otp) setDevOtpHint(result.dev_otp)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resend code")
    } finally {
      setBusy(false)
      setBusyAction(null)
    }
  }

  const onResetPassword = async (e) => {
    e.preventDefault()
    setBusyAction("reset-confirm")
    setBusy(true)
    resetAlerts()
    try {
      if (newPassword.length < 8) {
        throw new Error("Password must be at least 8 characters.")
      }
      await authApi.confirmPasswordReset({
        email: email.trim(),
        otp,
        newPassword,
      })
      await login({ email: email.trim(), password: newPassword })
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset password")
    } finally {
      setBusy(false)
      setBusyAction(null)
    }
  }

  const titles = {
    email: "Welcome to Career OS",
    login: "Sign in",
    onboarding: "Create your account",
    forgot: "Reset password",
  }

  const descriptions = {
    email: "Enter your email to continue",
    login: `Signing in as ${email}`,
    onboarding: "Just a few details to get started",
    forgot: otpSent
      ? `Enter the code sent to ${email}`
      : "We'll email you a verification code",
  }

  if (!open) return null

  return (
    <AppModal
      open={open}
      onClose={handleClose}
      placement="center"
      backdrop={backdrop}
      panelVariant={panelVariant}
      size="md"
      showClose={!busy}
      closeOnBackdrop={!busy}
      title={null}
      description={null}
    >
      <AuthBrand dark={isCredentialsStep} />
      <div className="text-center">
        <h2
          className={cn(
            "text-xl font-semibold tracking-tight sm:text-2xl",
            isCredentialsStep ? "text-foreground" : "text-slate-900"
          )}
        >
          {step === "login"
            ? `Hi ${displayName || "there"}`
            : titles[step]}
        </h2>
        <p
          className={cn(
            "mt-1 text-sm",
            isCredentialsStep ? "text-muted-foreground" : "text-slate-600"
          )}
        >
          {descriptions[step]}
        </p>
      </div>

      {step === "email" && waking ? (
        <div className="mt-4">
          <SlowLoadingFormHint active messageKey="backend-wake" tone="light" />
        </div>
      ) : null}

      {step === "email" && failed && !waking ? (
        <div className="mt-4 rounded-lg border border-amber-300/80 bg-amber-50 px-3 py-2.5 text-sm text-amber-950">
          <p className="font-medium">Could not reach the API</p>
          <p className="mt-1 text-xs text-amber-900/90">
            Render cold starts can take up to a minute. Check{" "}
            <code className="rounded bg-amber-100/80 px-1">VITE_API_BASE_URL</code> on Vercel.
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="landing-btn-outline mt-3"
            onClick={() => void retryWake()}
          >
            Retry connection
          </Button>
        </div>
      ) : null}

      {step !== "email" ? (
        <button
          type="button"
          className="mt-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          onClick={step === "forgot" ? () => setStep("login") : goEmail}
          disabled={busy}
        >
          <ArrowLeft className="size-4" />
          Back
        </button>
      ) : null}

      {step === "email" ? (
        <form onSubmit={onEmailContinue} className="mt-4 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-800">Email</label>
            <input
              type="email"
              required
              autoFocus
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={landingInputClass}
              placeholder="you@company.com"
            />
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <SlowLoadingFormHint
            active={busy}
            messageKey={busyAction || "check-email"}
            tone="light"
          />
          <WakeAwareButton
            type="submit"
            className="landing-btn-primary w-full"
            disabled={busy}
            tooltipSide="right"
          >
            {busy ? <Loader2 className="size-4 animate-spin" /> : null}
            Continue
          </WakeAwareButton>
        </form>
      ) : null}

      {step === "login" ? (
        <form onSubmit={onLogin} className="mt-4 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Password</label>
            <PasswordInput
              required
              autoFocus
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              inputClassName={authInputClass}
            />
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              className="text-sm text-primary hover:underline"
              onClick={startForgot}
              disabled={busy}
            >
              Forgot password?
            </button>
          </div>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <SlowLoadingFormHint active={busy} messageKey={busyAction || "login"} />
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : null}
            Sign in
          </Button>
        </form>
      ) : null}

      {step === "onboarding" ? (
        <form onSubmit={onOnboarding} className="mt-4 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Your name</label>
            <input
              required
              autoFocus
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={authInputClass}
              placeholder="How should we address you?"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Create password</label>
            <PasswordInput
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              inputClassName={authInputClass}
            />
            <p className="text-xs text-muted-foreground">At least 8 characters</p>
          </div>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <SlowLoadingFormHint active={busy} messageKey={busyAction || "register"} />
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : null}
            Get started
          </Button>
        </form>
      ) : null}

      {step === "forgot" ? (
        <form onSubmit={onResetPassword} className="mt-4 space-y-4">
          {message ? (
            <p className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-400">
              {message}
            </p>
          ) : null}
          {devOtpHint ? (
            <p className="text-xs text-muted-foreground">Dev code: {devOtpHint}</p>
          ) : null}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Verification code</label>
            <input
              inputMode="numeric"
              pattern="[0-9]*"
              required
              autoFocus
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
              className={authInputClass}
              placeholder="6-digit code"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">New password</label>
            <PasswordInput
              required
              minLength={8}
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              inputClassName={authInputClass}
            />
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              className="text-sm text-primary hover:underline"
              onClick={resendOtp}
              disabled={busy}
            >
              Resend code
            </button>
          </div>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <SlowLoadingFormHint
            active={busy}
            messageKey={busyAction === "reset-confirm" ? "reset-confirm" : "reset-send"}
          />
          <Button type="submit" className="w-full" disabled={busy || !otpSent}>
            Update password & sign in
          </Button>
        </form>
      ) : null}
    </AppModal>
  )
}
