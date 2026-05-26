import { cn } from "@/lib/utils"

/**
 * Responsive job card grid (flex/grid) — avoids virtualized overlap on tall cards.
 */
export function VirtualizedJobGrid({ jobs, renderCard, className }) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3",
        className
      )}
    >
      {jobs.map((job) => (
        <div key={job.id || job.job_id || `${job.title}-${job.company}`} className="min-w-0">
          {renderCard(job)}
        </div>
      ))}
    </div>
  )
}
