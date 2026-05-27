import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"

import { fetchBackendHealth, waitForBackendReady, wakeBackend } from "@/services/backendHealthService"

const BackendWakeContext = createContext(null)

/** Align with UptimeRobot 5-minute interval */
const KEEPALIVE_MS = 5 * 60 * 1000

/**
 * @typedef {'checking' | 'online' | 'reconnecting' | 'sleeping' | 'error'} BackendConnectionStatus
 */

export function BackendWakeProvider({ children }) {
  /** @type {[BackendConnectionStatus, Function]} */
  const [status, setStatus] = useState("checking")
  const [health, setHealth] = useState(null)
  const wasOnlineRef = useRef(false)

  const applyHealthResult = useCallback((result) => {
    if (!result.ok) {
      setHealth(null)
      if (wasOnlineRef.current) {
        setStatus("sleeping")
      } else {
        setStatus("error")
      }
      return false
    }
    wasOnlineRef.current = true
    setHealth(result.data ?? null)
    setStatus("online")
    return true
  }, [])

  const ping = useCallback(async () => {
    const result = await fetchBackendHealth(12000)
    return applyHealthResult(result)
  }, [applyHealthResult])

  const ensureReady = useCallback(async () => {
    if (wasOnlineRef.current) {
      setStatus("reconnecting")
    } else {
      setStatus("checking")
    }
    wakeBackend()
    const ok = await waitForBackendReady({ maxAttempts: 45, intervalMs: 2000 })
    if (ok) {
      wasOnlineRef.current = true
      setStatus("online")
      const result = await fetchBackendHealth(12000)
      if (result.ok) {
        setHealth(result.data ?? null)
      }
    } else if (wasOnlineRef.current) {
      setStatus("sleeping")
    } else {
      setStatus("error")
    }
    return ok
  }, [])

  useEffect(() => {
    ensureReady()
  }, [ensureReady])

  useEffect(() => {
    if (status !== "online" && status !== "sleeping") return undefined
    const timer = window.setInterval(() => {
      void ping()
    }, KEEPALIVE_MS)
    return () => window.clearInterval(timer)
  }, [status, ping])

  const value = useMemo(
    () => ({
      status,
      health,
      ready: status === "online",
      online: status === "online",
      waking: status === "checking" || status === "reconnecting",
      sleeping: status === "sleeping",
      failed: status === "error",
      retryWake: ensureReady,
      ping,
    }),
    [status, health, ensureReady, ping]
  )

  return (
    <BackendWakeContext.Provider value={value}>{children}</BackendWakeContext.Provider>
  )
}

export function useBackendWake() {
  const ctx = useContext(BackendWakeContext)
  if (!ctx) {
    return {
      status: "online",
      health: null,
      ready: true,
      online: true,
      waking: false,
      sleeping: false,
      failed: false,
      retryWake: async () => true,
      ping: async () => true,
    }
  }
  return ctx
}
