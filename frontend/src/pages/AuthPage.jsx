import { useState } from "react"
import { ArrowLeft, Briefcase, Loader2 } from "lucide-react"

import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import * as authApi from "@/services/authService"

const inputClass =
  "flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm"

function detectTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Kolkata"
  } catch {
    return "Asia/Kolkata"
  }
}

export function AuthPage({ onBack }) {
  const { login, register } = useAuth()
  const [step, setStep] = useState("email")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [otp, setOtp] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [otpSent, setOtpSent] = useState(false)
  const [devOtpHint, setDevOtpHint] = useState("")
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)

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
    resetAlerts()
  }

  const onEmailContinue = async (e) => {
    e.preventDefault()
    setBusy(true)
    resetAlerts()
    try {
      const result = await authApi.checkEmail(email.trim())
      setStep(result.exists ? "login" : "onboarding")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not verify email")
    } finally {
      setBusy(false)
    }
  }

  const onLogin = async (e) => {
    e.preventDefault()
    setBusy(true)
    resetAlerts()
    try {
      await login({ email: email.trim(), password })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed")
    } finally {
      setBusy(false)
    }
  }

  const onOnboarding = async (e) => {
    e.preventDefault()
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account")
    } finally {
      setBusy(false)
    }
  }

  const startForgot = async () => {
    setStep("forgot")
    setOtp("")
    setNewPassword("")
    setOtpSent(false)
    setDevOtpHint("")
    resetAlerts()
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
    }
  }

  const resendOtp = async () => {
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
    }
  }

  const onResetPassword = async (e) => {
    e.preventDefault()
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset password")
    } finally {
      setBusy(false)
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

  return (
    <div className="neon-app-shell relative flex min-h-svh items-center justify-center p-4">
      <Card className="neon-glass relative z-10 w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="neon-glow-sm mx-auto flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
            <Briefcase className="size-6" />
          </div>
          <CardTitle className="text-2xl">{titles[step]}</CardTitle>
          <CardDescription>{descriptions[step]}</CardDescription>
        </CardHeader>
        <CardContent>
          {step === "email" && onBack ? (
            <button
              type="button"
              className="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              onClick={onBack}
            >
              <ArrowLeft className="size-4" />
              Back to home
            </button>
          ) : step !== "email" ? (
            <button
              type="button"
              className="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              onClick={step === "forgot" ? () => setStep("login") : goEmail}
            >
              <ArrowLeft className="size-4" />
              Back
            </button>
          ) : null}

          {step === "email" ? (
            <form onSubmit={onEmailContinue} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Email</label>
                <input
                  type="email"
                  required
                  autoFocus
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClass}
                  placeholder="you@company.com"
                />
              </div>
              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={busy}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                Continue
              </Button>
            </form>
          ) : null}

          {step === "login" ? (
            <form onSubmit={onLogin} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Password</label>
                <input
                  type="password"
                  required
                  autoFocus
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputClass}
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
              <Button type="submit" className="w-full" disabled={busy}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                Sign in
              </Button>
            </form>
          ) : null}

          {step === "onboarding" ? (
            <form onSubmit={onOnboarding} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Your name</label>
                <input
                  required
                  autoFocus
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className={inputClass}
                  placeholder="How should we address you?"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Create password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputClass}
                />
                <p className="text-xs text-muted-foreground">At least 8 characters</p>
              </div>
              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={busy}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                Get started
              </Button>
            </form>
          ) : null}

          {step === "forgot" ? (
            <form onSubmit={onResetPassword} className="space-y-4">
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
                  className={inputClass}
                  placeholder="6-digit code"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">New password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className={inputClass}
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
              <Button type="submit" className="w-full" disabled={busy || !otpSent}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                Update password & sign in
              </Button>
            </form>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
