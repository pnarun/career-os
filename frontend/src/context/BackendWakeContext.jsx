import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { pingBackendHealth, waitForBackendReady, wakeBackend } from "@/services/backendHealthService"

const BackendWakeContext = createContext(null)

const KEEPALIVE_MS = 12 * 60 * 1000

export function BackendWakeProvider({ children }) {
  const [status, setStatus] = useState("checking")

  const ensureReady = useCallback(async () => {
    setStatus("checking")
    wakeBackend()
    const ok = await waitForBackendReady({ maxAttempts: 45, intervalMs: 2000 })
    setStatus(ok ? "ready" : "error")
    return ok
  }, [])

  useEffect(() => {
    ensureReady()
  }, [ensureReady])

  useEffect(() => {
    if (status !== "ready") return undefined
    const timer = window.setInterval(() => {
      void pingBackendHealth(12000)
    }, KEEPALIVE_MS)
    return () => window.clearInterval(timer)
  }, [status])

  const value = useMemo(
    () => ({
      status,
      ready: status === "ready",
      waking: status === "checking",
      failed: status === "error",
      retryWake: ensureReady,
    }),
    [status, ensureReady]
  )

  return (
    <BackendWakeContext.Provider value={value}>{children}</BackendWakeContext.Provider>
  )
}

export function useBackendWake() {
  const ctx = useContext(BackendWakeContext)
  if (!ctx) {
    return {
      status: "ready",
      ready: true,
      waking: false,
      failed: false,
      retryWake: async () => true,
    }
  }
  return ctx
}
