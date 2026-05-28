import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function JobListPagination({
  page,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  className,
}) {
  if (totalItems === 0) return null

  const start = (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, totalItems)
  const showPager = totalPages > 1

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-between gap-3 border-t border-border/60 pt-4 sm:flex-row",
        className
      )}
    >
      <p className="text-xs text-muted-foreground tabular-nums">
        Showing {start}–{end} of {totalItems}
      </p>
      {showPager ? (
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </Button>
          <span className="min-w-[5rem] text-center text-xs text-muted-foreground tabular-nums">
            Page {page} / {totalPages}
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </Button>
        </div>
      ) : (
        <span className="text-xs text-muted-foreground tabular-nums">Page 1 / 1</span>
      )}
    </div>
  )
}
