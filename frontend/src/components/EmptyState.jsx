import { cn } from "@/lib/utils"

/**
 * Shared empty state — encouraging, calm, consistent across hubs.
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  children,
  className,
}) {
  return (
    <div
      className={cn(
        "flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border/70 bg-muted/10 px-6 py-10 text-center",
        className
      )}
    >
      {Icon ? (
        <span className="flex size-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400">
          <Icon className="size-6" aria-hidden />
        </span>
      ) : null}
      <div className="max-w-md space-y-1.5">
        <p className="text-sm font-medium text-foreground">{title}</p>
        {description ? (
          <p className="text-xs leading-relaxed text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {children ? <div className="mt-1 flex flex-wrap justify-center gap-2">{children}</div> : null}
    </div>
  )
}
