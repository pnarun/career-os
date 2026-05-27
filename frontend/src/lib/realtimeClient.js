import { getAccessToken, getApiBaseUrl, refreshAccessToken } from "./apiClient"

const RECONNECT_BASE_MS = 1500
const RECONNECT_MAX_MS = 30000

function wsBaseUrl() {
  const env = import.meta.env.VITE_WS_BASE_URL
  if (env) return env.replace(/\/$/, "")
  const http = getApiBaseUrl().replace(/\/$/, "")
  return http.replace(/^http/, "ws")
}

export class RealtimeClient {
  constructor() {
    this.ws = null
    this.handlers = new Set()
    this.reconnectTimer = null
    this.reconnectAttempts = 0
    this.shouldConnect = false
    this.pingTimer = null
  }

  connect() {
    const token = getAccessToken()
    if (!token) return

    this.shouldConnect = true
    this._clearReconnect()

    if (this.ws?.readyState === WebSocket.OPEN) return

    const url = `${wsBaseUrl()}/ws/realtime?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    this.ws = ws

    ws.onopen = () => {
      this.reconnectAttempts = 0
      this._startPing()
    }

    const emitDisconnected = () => {
      this.handlers.forEach((handler) => {
        try {
          handler({ event: "disconnected" })
        } catch {
          /* ignore */
        }
      })
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.event === "pong") return
        this.handlers.forEach((handler) => {
          try {
            handler(payload)
          } catch {
            /* ignore handler errors */
          }
        })
      } catch {
        /* ignore malformed payloads */
      }
    }

    ws.onclose = async (event) => {
      this._stopPing()
      this.ws = null
      emitDisconnected()
      if (!this.shouldConnect) return

      const authRejected = event.code === 4401 || event.code === 4403
      if (authRejected) {
        const newToken = await refreshAccessToken()
        if (newToken) {
          this.reconnectAttempts = 0
          this.connect()
          return
        }
        this.shouldConnect = false
        return
      }

      this._scheduleReconnect()
    }

    ws.onerror = () => {
      ws.close()
    }
  }

  disconnect() {
    this.shouldConnect = false
    this._clearReconnect()
    this._stopPing()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  subscribe(handler) {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  _startPing() {
    this._stopPing()
    this.pingTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping")
      }
    }, 25000)
  }

  _stopPing() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }

  _scheduleReconnect() {
    this._clearReconnect()
    const delay = Math.min(
      RECONNECT_BASE_MS * 2 ** this.reconnectAttempts,
      RECONNECT_MAX_MS
    )
    this.reconnectAttempts += 1
    this.reconnectTimer = window.setTimeout(() => this.connect(), delay)
  }

  _clearReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

export const realtimeClient = new RealtimeClient()
