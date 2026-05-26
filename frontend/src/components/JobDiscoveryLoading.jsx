import { JOB_DISCOVERY_MESSAGES } from "@/data/loadingMessages"
import { SlowLoadingInline, SlowLoadingPanel } from "@/components/SlowLoadingStatus"

/** Full-page style loader for Jobs feed discovery. */
export function JobDiscoveryLoading({ className, active = true }) {
  return (
    <SlowLoadingPanel
      active={active}
      messages={JOB_DISCOVERY_MESSAGES}
      className={className}
    />
  )
}

/** Inline status line (scan summary bar). */
export function JobDiscoveryLoadingInline({ active = true }) {
  return (
    <SlowLoadingInline active={active} messages={JOB_DISCOVERY_MESSAGES} />
  )
}
