import { SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"
import { cn } from "@/lib/utils"

export function PageSectionSkeleton({ lines = 3, className }) {
  return (
    <div className={cn("animate-pulse space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-10 rounded-lg bg-muted/40" />
      ))}
    </div>
  )
}

/** Same branded loader as Resume AI / scan center — rotating analytics copy. */
export function AnalyticsPageSkeleton() {
  return (
    <SlowLoadingPageCenter
      active
      messageKey="career-analytics"
      delayMs={0}
      className="min-h-[50vh]"
    />
  )
}
