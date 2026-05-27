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

const MAX_TIMELINE = 80
const MAX_TOASTS = 5
const FEED_BUMP_DEBOUNCE_MS = 450

const ConnectionContext = createContext({ connected: false })
const FeedVersionContext = createContext(0)
const NotificationVersionContext = createContext(0)
const TimelineContext = createContext({
  timeline: [],
  clearTimeline: () => {},
  scanActive: false,
})
const ToastContext = createContext({
  toasts: [],
  dismissToast: () => {},
})

export function RealtimeProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [connected, setConnected] = useState(false)
  const [timeline, setTimeline] = useState([])
  const [toasts, setToasts] = useState([])
  const [feedVersion, setFeedVersion] = useState(0)
  const [notificationVersion, setNotificationVersion] = useState(0)
  const scanActiveRef = useRef(false)
  const feedBumpTimerRef = useRef(null)

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

  const bumpFeedVersion = useCallback(() => {
    if (feedBumpTimerRef.current) {
      window.clearTimeout(feedBumpTimerRef.current)
    }
    feedBumpTimerRef.current = window.setTimeout(() => {
      setFeedVersion((v) => v + 1)
      feedBumpTimerRef.current = null
    }, FEED_BUMP_DEBOUNCE_MS)
  }, [])

  const dismissToast = useCallback(
    (id) => setToasts((prev) => prev.filter((t) => t.id !== id)),
    []
  )

  const handleEvent = useCallback(
    (payload) => {
      const { event, message, timestamp } = payload

      if (event === "connected") {
        setConnected(true)
        return
      }

      if (event === "disconnected") {
        setConnected(false)
        return
      }

      if (event === "provider_batch") {
        const providers = payload.providers || []
        for (const item of providers) {
          pushTimeline({
            event: "provider_status",
            message: item.error || `${item.provider} ${item.status}`,
            timestamp: timestamp || new Date().toISOString(),
            data: item,
          })
        }
        bumpFeedVersion()
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
        bumpFeedVersion()
      } else if (event === "jobs_fetched" || event === "ai_scoring_complete") {
        bumpFeedVersion()
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
    [pushTimeline, pushToast, bumpFeedVersion]
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
      if (feedBumpTimerRef.current) {
        window.clearTimeout(feedBumpTimerRef.current)
      }
    }
  }, [isAuthenticated, handleEvent])

  const connectionValue = useMemo(() => ({ connected }), [connected])
  const timelineValue = useMemo(
    () => ({
      timeline,
      clearTimeline,
      scanActive: scanActiveRef.current,
    }),
    [timeline, clearTimeline]
  )
  const toastValue = useMemo(
    () => ({ toasts, dismissToast }),
    [toasts, dismissToast]
  )

  return (
    <ConnectionContext.Provider value={connectionValue}>
      <FeedVersionContext.Provider value={feedVersion}>
        <NotificationVersionContext.Provider value={notificationVersion}>
          <TimelineContext.Provider value={timelineValue}>
            <ToastContext.Provider value={toastValue}>{children}</ToastContext.Provider>
          </TimelineContext.Provider>
        </NotificationVersionContext.Provider>
      </FeedVersionContext.Provider>
    </ConnectionContext.Provider>
  )
}

export function useRealtime() {
  const connected = useContext(ConnectionContext).connected
  const feedVersion = useContext(FeedVersionContext)
  const notificationVersion = useContext(NotificationVersionContext)
  const { timeline, clearTimeline, scanActive } = useContext(TimelineContext)
  const { toasts, dismissToast } = useContext(ToastContext)
  return {
    connected,
    feedVersion,
    notificationVersion,
    timeline,
    clearTimeline,
    scanActive,
    toasts,
    dismissToast,
  }
}

export function useRealtimeOptional() {
  return useRealtime()
}

/** Subscribe only to feed refresh signals — avoids timeline/toast rerenders. */
export function useFeedVersion() {
  return useContext(FeedVersionContext)
}

/** Subscribe only to notification refresh signals. */
export function useNotificationVersion() {
  return useContext(NotificationVersionContext)
}

export function useRealtimeTimeline() {
  return useContext(TimelineContext)
}

export function useRealtimeToasts() {
  return useContext(ToastContext)
}

export function useRealtimeConnection() {
  return useContext(ConnectionContext)
}
