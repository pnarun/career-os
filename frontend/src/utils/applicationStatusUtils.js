export const STATUS_BADGE_STYLES = {
  saved: "bg-slate-500/10 text-slate-300 border-slate-500/30",
  applied: "bg-blue-500/10 text-blue-300 border-blue-500/30",
  interview: "bg-violet-500/10 text-violet-300 border-violet-500/30",
  assessment: "bg-indigo-500/10 text-indigo-300 border-indigo-500/30",
  rejected: "bg-red-500/10 text-red-300 border-red-500/30",
  offer: "bg-green-500/10 text-green-400 border-green-500/30",
  ghosted: "bg-orange-500/10 text-orange-300 border-orange-500/30",
  withdrawn: "bg-muted text-muted-foreground border-border",
}

export const STATUS_LABELS = {
  saved: "Saved",
  applied: "Applied",
  interview: "Interview Scheduled",
  assessment: "Assessment",
  rejected: "Rejected",
  offer: "Offer Received",
  ghosted: "Ghosted",
  withdrawn: "Withdrawn",
}

export function getStatusLabel(status) {
  return STATUS_LABELS[status] || status || "Unknown"
}

export function getStatusBadgeStyle(status) {
  return STATUS_BADGE_STYLES[status] || STATUS_BADGE_STYLES.saved
}

export function formatApplicationDate(iso) {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}
