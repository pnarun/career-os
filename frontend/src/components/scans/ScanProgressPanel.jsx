import { CheckCircle2, Loader2, XCircle } from "lucide-react"

import { cn } from "@/lib/utils"

const PROVIDER_ORDER = ["linkedin", "remoteok", "arbeitnow", "indeed", "naukri", "instahyre"]

function providerLabel(name) {
  if (!name) return "—"
  return name.charAt(0).toUpperCase() + name.slice(1)
}

function ProviderRow({ name, slot }) {
  const status = slot?.status || "pending"
  const Icon =
    status === "completed" ? CheckCircle2 : status === "failed" ? XCircle : Loader2
  const color =
    status === "completed"
      ? "text-emerald-400"
      : status === "failed"
        ? "text-red-400"
        : status === "running"
          ? "text-sky-400"
          : "text-muted-foreground"

  return (
    <li className="flex items-center justify-between gap-2 text-xs">
      <span className="flex min-w-0 items-center gap-2">
        <Icon className={cn("size-3.5 shrink-0", status === "running" && "animate-spin", color)} />
        <span className="truncate">{providerLabel(name)}</span>
      </span>
      <span className="shrink-0 tabular-nums text-muted-foreground">
        {status === "completed" || status === "failed"
          ? `${slot?.jobs_found ?? 0} jobs`
          : status === "running"
            ? "…"
            : "—"}
      </span>
    </li>
  )
}

/**
 * Live scan progress from WebSocket / poll status (no layout redesign).
 */
export function ScanProgressPanel({ status, className }) {
  if (!status) return null

  const providers = status.providers || {}
  const names = [
    ...PROVIDER_ORDER.filter((p) => providers[p]),
    ...Object.keys(providers).filter((p) => !PROVIDER_ORDER.includes(p)),
  ]

  return (
    <div
      className={cn(
        "rounded-lg border border-border/60 bg-muted/15 px-3 py-2.5 text-sm",
        className
      )}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-foreground">
          {status.current_provider
            ? `Active: ${providerLabel(status.current_provider)}`
            : "Scan progress"}
        </p>
        <p className="text-xs tabular-nums text-muted-foreground">
          {status.progress ?? 0}% · {status.jobs_found ?? 0} jobs found
        </p>
      </div>
      {names.length > 0 ? (
        <ul className="grid gap-1 sm:grid-cols-2">
          {names.map((name) => (
            <ProviderRow key={name} name={name} slot={providers[name]} />
          ))}
        </ul>
      ) : null}
      {(status.providers_failed || []).length > 0 ? (
        <p className="mt-2 text-[11px] text-amber-400">
          Partial success — failed: {(status.providers_failed || []).join(", ")}
        </p>
      ) : null}
    </div>
  )
}
