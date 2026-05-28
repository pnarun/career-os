import { memo } from "react"
import type { LucideIcon } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

type StatCardProps = {
  title: string
  value: string
  description: string
  icon: LucideIcon
  onClick?: () => void
  accent?: string
}

export const StatCard = memo(function StatCard({
  title,
  value,
  description,
  icon: Icon,
  onClick,
  accent,
}: StatCardProps) {
  const clickable = Boolean(onClick)

  return (
    <Card
      className={cn(
        "transition-colors",
        clickable && "cursor-pointer hover:border-primary/40 hover:bg-muted/30"
      )}
      onClick={onClick}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      onKeyDown={
        clickable
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                onClick?.()
              }
            }
          : undefined
      }
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-1">
          <CardDescription>{title}</CardDescription>
          <CardTitle className={cn("text-2xl font-semibold tabular-nums", accent)}>
            {value}
          </CardTitle>
        </div>
        <div className="flex size-9 items-center justify-center rounded-lg bg-muted">
          <Icon className="size-4 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
})
