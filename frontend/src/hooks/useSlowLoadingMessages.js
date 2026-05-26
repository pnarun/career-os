import { useEffect, useState } from "react"

import { GENERIC_WAIT_MESSAGES } from "@/data/loadingMessages"

const DEFAULT_DELAY_MS = 2000
const DEFAULT_INTERVAL_MS = 4500

export function useRotatingMessage(messages, intervalMs = DEFAULT_INTERVAL_MS) {
  const pool = messages?.length ? messages : GENERIC_WAIT_MESSAGES
  const [index, setIndex] = useState(0)

  useEffect(() => {
    setIndex(0)
  }, [messages])

  useEffect(() => {
    if (pool.length <= 1) return undefined
    const timer = setInterval(
      () => setIndex((current) => (current + 1) % pool.length),
      intervalMs
    )
    return () => clearInterval(timer)
  }, [pool, intervalMs])

  return { message: pool[index] ?? pool[0], index, count: pool.length }
}

/**
 * After `delayMs`, expose rotating messages while `active` is true.
 * Fast responses never flash the slow UI.
 */
export function useSlowLoadingMessages(
  active,
  messages,
  { delayMs = DEFAULT_DELAY_MS, intervalMs = DEFAULT_INTERVAL_MS } = {}
) {
  const [showSlow, setShowSlow] = useState(false)
  const { message, index, count } = useRotatingMessage(messages, intervalMs)

  useEffect(() => {
    if (!active) {
      setShowSlow(false)
      return undefined
    }
    const timer = window.setTimeout(() => setShowSlow(true), delayMs)
    return () => {
      window.clearTimeout(timer)
      setShowSlow(false)
    }
  }, [active, delayMs])

  return { showSlow: active && showSlow, message, index, count }
}
