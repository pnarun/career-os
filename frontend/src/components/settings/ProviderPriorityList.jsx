import { useState } from "react"
import { GripVertical } from "lucide-react"

import { cn } from "@/lib/utils"

function reorderList(list, fromId, toId) {
  const from = list.indexOf(fromId)
  const to = list.indexOf(toId)
  if (from < 0 || to < 0 || from === to) return list
  const next = [...list]
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}

/**
 * @param {{
 *   order: string[]
 *   enabledIds: string[]
 *   providersById: Record<string, { id: string, label: string }>
 *   onReorder: (fromId: string, toId: string) => void
 *   onToggle: (id: string) => void
 * }} props
 */
export function ProviderPriorityList({
  order,
  enabledIds,
  providersById,
  onReorder,
  onToggle,
}) {
  const [dragId, setDragId] = useState(null)
  const [overId, setOverId] = useState(null)

  const endDrag = () => {
    setDragId(null)
    setOverId(null)
  }

  const handleDragStart = (event, id) => {
    setDragId(id)
    event.dataTransfer.effectAllowed = "move"
    event.dataTransfer.setData("text/plain", id)
  }

  const handleDragOver = (event, id) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
    if (dragId && id !== dragId) setOverId(id)
  }

  const handleDrop = (event, targetId) => {
    event.preventDefault()
    const sourceId = dragId || event.dataTransfer.getData("text/plain")
    if (sourceId && sourceId !== targetId) onReorder(sourceId, targetId)
    endDrag()
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        Drag the handle to set fetch priority. Higher items run first.
      </p>
      <ul className="space-y-2" role="list">
        {order.map((id, index) => {
          const provider = providersById[id] || { id, label: id }
          const isDragging = dragId === id
          const isDropTarget = overId === id && dragId !== id
          const enabled = enabledIds.includes(id)

          return (
            <li
              key={id}
              draggable
              onDragStart={(e) => handleDragStart(e, id)}
              onDragOver={(e) => handleDragOver(e, id)}
              onDragLeave={() => {
                if (overId === id) setOverId(null)
              }}
              onDrop={(e) => handleDrop(e, id)}
              onDragEnd={endDrag}
              className={cn(
                "flex items-center gap-2 rounded-lg border border-border bg-muted/10 px-2 py-2 transition-colors",
                isDragging && "opacity-50",
                isDropTarget && "border-primary/50 bg-primary/5 ring-1 ring-primary/30"
              )}
            >
              <button
                type="button"
                className="cursor-grab touch-none p-1 text-muted-foreground hover:text-foreground active:cursor-grabbing"
                aria-label={`Drag to reorder ${provider.label}`}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <GripVertical className="size-4" />
              </button>
              <input
                type="checkbox"
                checked={enabled}
                onChange={() => onToggle(id)}
                aria-label={`Enable ${provider.label}`}
              />
              <span className={cn("flex-1 text-sm", !enabled && "text-muted-foreground")}>
                {provider.label}
              </span>
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs tabular-nums text-muted-foreground">
                #{index + 1}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export { reorderList }
