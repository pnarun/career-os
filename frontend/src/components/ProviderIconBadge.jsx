import { cn } from "@/lib/utils"
import { getSourceLabel } from "@/utils/jobLocationUtils"
import { getProviderIconMeta } from "@/utils/providerIconUtils"

/**
 * @param {{ source?: string, className?: string }} props
 */
export function ProviderIconBadge({ source, className = "" }) {
  const meta = getProviderIconMeta(source)
  const label = getSourceLabel({ source })

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold",
        meta.className,
        className
      )}
      title={label}
    >
      <span className="inline-flex size-4 items-center justify-center rounded-sm bg-black/10 text-[10px] font-bold">
        {meta.label}
      </span>
      {label}
    </span>
  )
}
