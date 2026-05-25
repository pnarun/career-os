import { AlertTriangle, CheckCircle2, Clock, ShieldAlert } from "lucide-react"

import { cn } from "@/lib/utils"
import { getSourceLabel } from "@/utils/jobLocationUtils"
import {
  getProviderErrorLabel,
  getProviderStatusList,
  getProviderStatusStyle,
} from "@/utils/providerStatusUtils"

/**
 * @param {{ diagnostic: Record<string, unknown> }} props
 */
function ProviderStatusBadge({ diagnostic }) {
  const source = String(diagnostic.source || "")
  const status = String(diagnostic.status || "failed")
  const jobsFetched = Number(diagnostic.jobs_fetched ?? 0)
  const durationMs = Number(diagnostic.duration_ms ?? 0)
  const errorType = String(diagnostic.error_type || "none")
  const errorMessage = String(diagnostic.error_message || "")
  const requiresAuth = Boolean(diagnostic.requires_auth)
  const sessionValid = diagnostic.session_valid

  const isSuccess = status === "success"

  return (
    <div
      className={cn(
        "rounded-lg border px-3 py-2.5 text-xs",
        getProviderStatusStyle(diagnostic)
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">{getSourceLabel({ source })}</span>
        <span className="inline-flex items-center gap-1 capitalize">
          {isSuccess ? (
            <CheckCircle2 className="size-3.5" />
          ) : status === "skipped" ? null : (
            <AlertTriangle className="size-3.5" />
          )}
          {status}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] opacity-90">
        <span className="tabular-nums">{jobsFetched} jobs</span>
        {durationMs > 0 && (
          <span className="inline-flex items-center gap-0.5 tabular-nums">
            <Clock className="size-3" />
            {durationMs}ms
          </span>
        )}
        {requiresAuth && (
          <span className="inline-flex items-center gap-0.5">
            <ShieldAlert className="size-3" />
            Auth required
          </span>
        )}
        {sessionValid === false && <span>Session invalid</span>}
        {sessionValid === true && <span>Session OK</span>}
      </div>

      {!isSuccess && errorType !== "none" && (
        <p className="mt-2 font-medium">{getProviderErrorLabel(errorType)}</p>
      )}

      {!isSuccess && errorMessage && (
        <p className="mt-1 leading-snug opacity-90">{errorMessage}</p>
      )}
    </div>
  )
}

/**
 * @param {{
 *   summary: Record<string, unknown> | null
 *   className?: string
 * }} props
 */
export function ProviderStatusPanel({ summary, className }) {
  const providers = getProviderStatusList(summary)

  if (!providers.length) return null

  const failedCount = providers.filter((p) => p.status !== "success").length

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center gap-2">
        <AlertTriangle
          className={cn(
            "size-4",
            failedCount > 0 ? "text-amber-400" : "text-green-400"
          )}
        />
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Provider status
          {failedCount > 0 && (
            <span className="ml-2 font-normal normal-case text-amber-400">
              {failedCount} need attention
            </span>
          )}
        </h4>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {providers.map((diagnostic) => (
          <ProviderStatusBadge
            key={String(diagnostic.source)}
            diagnostic={diagnostic}
          />
        ))}
      </div>
    </div>
  )
}
