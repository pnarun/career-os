import { useMemo } from "react"

import { JobListPagination } from "@/components/JobListPagination"
import { cn } from "@/lib/utils"

export const JOBS_PAGE_SIZE = 6

function PlainJobGrid({ jobs, renderCard, className }) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3",
        className
      )}
    >
      {jobs.map((job) => (
        <div
          key={job.id || job.job_id || `${job.title}-${job.company}`}
          className="min-w-0 self-start"
        >
          {renderCard(job)}
        </div>
      ))}
    </div>
  )
}

/**
 * Paginated job grid (6 cards per page). Uses a normal CSS grid so card heights never overlap.
 */
export function VirtualizedJobGrid({
  jobs,
  renderCard,
  className,
  page = 1,
  onPageChange,
  pageSize = JOBS_PAGE_SIZE,
}) {
  const totalPages = Math.max(1, Math.ceil(jobs.length / pageSize) || 1)
  const safePage = Math.min(Math.max(1, page), totalPages)

  const pagedJobs = useMemo(() => {
    const start = (safePage - 1) * pageSize
    return jobs.slice(start, start + pageSize)
  }, [jobs, safePage, pageSize])

  return (
    <div className={cn("space-y-4", className)}>
      <PlainJobGrid jobs={pagedJobs} renderCard={renderCard} />
      <JobListPagination
        page={safePage}
        totalPages={totalPages}
        totalItems={jobs.length}
        pageSize={pageSize}
        onPageChange={onPageChange}
      />
    </div>
  )
}
