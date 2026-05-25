export const PROVIDER_ICONS = {
  linkedin: { label: "in", className: "bg-[#0A66C2]/15 text-[#0A66C2] border-[#0A66C2]/30" },
  instahyre: { label: "IH", className: "bg-purple-500/15 text-purple-300 border-purple-500/30" },
  naukri: { label: "Nk", className: "bg-blue-500/15 text-blue-300 border-blue-500/30" },
  indeed: { label: "Id", className: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30" },
  remoteok: { label: "RO", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  arbeitnow: { label: "AN", className: "bg-orange-500/15 text-orange-300 border-orange-500/30" },
}

const DEFAULT_ICON = {
  label: "?",
  className: "bg-muted text-muted-foreground border-border",
}

/**
 * @param {string} source
 */
export function getProviderIconMeta(source) {
  const key = String(source || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "")
  return PROVIDER_ICONS[key] ?? DEFAULT_ICON
}

/**
 * @param {string} iso
 */
export function formatPostedTime(iso) {
  if (!iso) return ""
  try {
    const date = new Date(iso)
    const diffMs = Date.now() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    if (diffHours < 1) return "Just now"
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
  } catch {
    return iso
  }
}
