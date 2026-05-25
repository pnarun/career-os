import { memo, useMemo } from "react"
import { Grid } from "react-window"

import { cn } from "@/lib/utils"

const CARD_HEIGHT = 520
const GAP = 16

function getColumnCount(width) {
  if (width >= 1280) return 3
  if (width >= 640) return 2
  return 1
}

function JobGridCell({ columnIndex, rowIndex, style, jobs, columnCount, renderCard }) {
  const index = rowIndex * columnCount + columnIndex
  if (index >= jobs.length) return null
  const job = jobs[index]
  return (
    <div
      style={{
        ...style,
        left: Number(style.left) + GAP / 2,
        top: Number(style.top) + GAP / 2,
        width: Number(style.width) - GAP,
        height: Number(style.height) - GAP,
      }}
    >
      {renderCard(job)}
    </div>
  )
}

const MemoCell = memo(JobGridCell)

/**
 * Virtualized grid for large job lists (react-window v2 Grid).
 */
export function VirtualizedJobGrid({ jobs, renderCard, className }) {
  const width = typeof window !== "undefined" ? window.innerWidth : 1200
  const columnCount = getColumnCount(width)
  const rowCount = Math.ceil(jobs.length / columnCount)
  const gridWidth = Math.min(width, 1152) - 32
  const columnWidth = Math.floor(gridWidth / columnCount)
  const gridHeight = Math.min(
    Math.max(rowCount * (CARD_HEIGHT + GAP), 400),
    typeof window !== "undefined" ? window.innerHeight * 0.75 : 800
  )

  const cellProps = useMemo(
    () => ({ jobs, columnCount, renderCard }),
    [jobs, columnCount, renderCard]
  )

  if (jobs.length <= 12) {
    return (
      <div className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-3", className)}>
        {jobs.map((job) => (
          <div key={job.id}>{renderCard(job)}</div>
        ))}
      </div>
    )
  }

  return (
    <div className={className}>
      <Grid
        cellComponent={MemoCell}
        cellProps={cellProps}
        columnCount={columnCount}
        columnWidth={columnWidth}
        defaultHeight={gridHeight}
        defaultWidth={gridWidth}
        rowCount={rowCount}
        rowHeight={CARD_HEIGHT + GAP}
        style={{ height: gridHeight, width: gridWidth }}
      />
    </div>
  )
}
