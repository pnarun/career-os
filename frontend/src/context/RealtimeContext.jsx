import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react"

import { useAuth } from "@/context/AuthContext"
import { realtimeClient } from "@/lib/realtimeClient"

const RealtimeContext = createContext(null)

const MAX_TIMELINE = 80
const MAX_TOASTS = 5

export function RealtimeProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [connected, setConnected] = useState(false)
  const [timeline, setTimeline] = useState([])
  const [toasts, setToasts] = useState([])
  const [feedVersion, setFeedVersion] = useState(0)
  const [notificationVersion, setNotificationVersion] = useState(0)
  const scanActiveRef = useRef(false)

  const pushTimeline = useCallback((entry) => {
    setTimeline((prev) => [...prev.slice(-(MAX_TIMELINE - 1)), entry])
  }, [])

  const pushToast = useCallback((toast) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    setToasts((prev) => [...prev.slice(-(MAX_TOASTS - 1)), { id, ...toast }])
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 6000)
  }, [])

  const clearTimeline = useCallback(() => setTimeline([]), [])

  const handleEvent = useCallback(
    (payload) => {
      const { event, message, timestamp } = payload

      if (event === "connected") {
        setConnected(true)
        return
      }

      const logMessage = message || event
      const scanEvents = new Set([
        "scan_started",
        "scan_progress",
        "scan_completed",
        "scan_failed",
        "provider_started",
        "provider_status",
        "jobs_fetched",
        "ai_scoring_complete",
        "email_delivered",
        "automation_started",
        "automation_finished",
      ])

      if (scanEvents.has(event)) {
        pushTimeline({
          event,
          message: logMessage,
          timestamp: timestamp || new Date().toISOString(),
          data: payload,
        })
      }

      if (event === "scan_started") {
        scanActiveRef.current = true
      }
      if (event === "scan_completed" || event === "scan_failed") {
        scanActiveRef.current = false
        setFeedVersion((v) => v + 1)
      }
      if (event === "jobs_fetched" || event === "ai_scoring_complete") {
        setFeedVersion((v) => v + 1)
      }

      if (event === "notification") {
        const n = payload.notification
        setNotificationVersion((v) => v + 1)
        pushToast({
          title: n?.title || "Notification",
          message: n?.message || "",
          priority: n?.priority || "normal",
          type: n?.type,
        })
      }
    },
    [pushTimeline, pushToast]
  )

  useEffect(() => {
    if (!isAuthenticated) {
      realtimeClient.disconnect()
      setConnected(false)
      return undefined
    }

    const unsub = realtimeClient.subscribe(handleEvent)
    realtimeClient.connect()

    return () => {
      unsub()
      realtimeClient.disconnect()
      setConnected(false)
    }
  }, [isAuthenticated, handleEvent])

  const value = useMemo(
    () => ({
      connected,
      timeline,
      toasts,
      feedVersion,
      notificationVersion,
      scanActive: scanActiveRef.current,
      pushTimeline,
      clearTimeline,
      dismissToast: (id) => setToasts((prev) => prev.filter((t) => t.id !== id)),
    }),
    [connected, timeline, toasts, feedVersion, notificationVersion, pushTimeline, clearTimeline]
  )

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext)
  if (!ctx) throw new Error("useRealtime must be used within RealtimeProvider")
  return ctx
}

export function useRealtimeOptional() {
  return useContext(RealtimeContext)
}
