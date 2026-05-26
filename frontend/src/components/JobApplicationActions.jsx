import { useEffect, useState } from "react"

import { useApplicationsMapOptional } from "@/context/ApplicationsMapContext"
import { Bookmark, Bot, CheckCircle2, Loader2, Mic, Sparkles } from "lucide-react"

import { ApplyAssistantModal } from "@/components/ApplyAssistantModal"
import { JobInterviewPrepModal } from "@/components/JobInterviewPrepModal"
import { JobResumeOptimizeModal } from "@/components/JobResumeOptimizeModal"
import { ActionTooltip } from "@/components/ui/ActionTooltip"
import { Button } from "@/components/ui/button"
import {
  APPLICATION_STATUSES,
  getApplications,
  markJobApplied,
  saveJobApplication,
  updateApplicationStatus,
} from "@/services/applicationService"
import { isLinkedInEasyApply, ASSISTED_APPLY_ENABLED } from "@/services/autoApplyService"
import { getStatusLabel } from "@/utils/applicationStatusUtils"
import { cn } from "@/lib/utils"

function IconAction({ label, onClick, disabled, children, className, variant = "outline" }) {
  return (
    <ActionTooltip label={label} side="top">
      <Button
        type="button"
        size="icon"
        variant={variant}
        disabled={disabled}
        aria-label={label}
        className={cn(
          "size-9 shrink-0 transition-all duration-200",
          "hover:border-indigo-400/50 hover:bg-indigo-500/15 hover:text-indigo-200 hover:shadow-md hover:shadow-indigo-950/30",
          "focus-visible:ring-2 focus-visible:ring-indigo-500/50",
          className
        )}
        onClick={onClick}
      >
        {children}
      </Button>
    </ActionTooltip>
  )
}

export function JobApplicationActions({ job, compact = false, iconOnly = false, onUpdated }) {
  const applicationsMap = useApplicationsMapOptional()
  const jobKey = String(job.id || job.job_id || "")
  const mappedApplication = applicationsMap?.applicationByJobId?.[jobKey] ?? null
  const [application, setApplication] = useState(mappedApplication)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [applyModalOpen, setApplyModalOpen] = useState(false)
  const [optimizeModalOpen, setOptimizeModalOpen] = useState(false)
  const [interviewModalOpen, setInterviewModalOpen] = useState(false)

  const canAssistedApply = ASSISTED_APPLY_ENABLED && isLinkedInEasyApply(job)

  useEffect(() => {
    if (applicationsMap) {
      setApplication(mappedApplication)
      onUpdated?.(mappedApplication)
      return undefined
    }
    let cancelled = false
    getApplications({ jobId: jobKey })
      .then((apps) => {
        if (!cancelled) {
          const next = apps[0] ?? null
          setApplication(next)
          onUpdated?.(next)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setApplication(null)
          onUpdated?.(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [applicationsMap, jobKey, mappedApplication, onUpdated])

  const onSave = async () => {
    setBusy(true)
    setError(null)
    try {
      const saved = await saveJobApplication(job)
      setApplication(saved)
      applicationsMap?.setApplicationForJob?.(jobKey, saved)
      onUpdated?.(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save job")
    } finally {
      setBusy(false)
    }
  }

  const onApply = async () => {
    setBusy(true)
    setError(null)
    try {
      const applied = await markJobApplied(job)
      setApplication(applied)
      applicationsMap?.setApplicationForJob?.(jobKey, applied)
      onUpdated?.(applied)
      if (job.apply_url) {
        window.open(String(job.apply_url), "_blank", "noopener,noreferrer")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to track apply")
    } finally {
      setBusy(false)
    }
  }

  const onStatusChange = async (status) => {
    if (!application?.application_id) return
    setBusy(true)
    setError(null)
    try {
      const updated = await updateApplicationStatus(application.application_id, status)
      setApplication(updated)
      applicationsMap?.setApplicationForJob?.(jobKey, updated)
      onUpdated?.(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status")
    } finally {
      setBusy(false)
    }
  }

  const onApplyComplete = async () => {
    try {
      const apps = await getApplications({ jobId: String(job.id || job.job_id || "") })
      const next = apps[0] ?? null
      setApplication(next)
      onUpdated?.(next)
    } catch {
      /* refresh optional */
    }
  }

  if (iconOnly) {
    return (
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <IconAction label="Save job" onClick={onSave} disabled={busy}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : <Bookmark className="size-4" />}
          </IconAction>
          <IconAction label="Prepare for interview" onClick={() => setInterviewModalOpen(true)} disabled={busy}>
            <Mic className="size-4" />
          </IconAction>
          <IconAction label="Optimize resume for this job" onClick={() => setOptimizeModalOpen(true)} disabled={busy}>
            <Sparkles className="size-4" />
          </IconAction>
          <IconAction label="Mark as applied" onClick={onApply} disabled={busy}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
          </IconAction>
          {canAssistedApply && (
            <IconAction
              label="Assisted apply (LinkedIn Easy Apply)"
              variant="default"
              className="border-indigo-500/40 bg-indigo-600/20 hover:bg-indigo-600/35"
              onClick={() => setApplyModalOpen(true)}
              disabled={busy}
            >
              <Bot className="size-4" />
            </IconAction>
          )}
        </div>
        {application && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-muted-foreground">Application:</span>
            <span className="font-medium">{getStatusLabel(application.status)}</span>
            <select
              value={application.status}
              onChange={(e) => onStatusChange(e.target.value)}
              disabled={busy}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs"
            >
              {APPLICATION_STATUSES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        )}
        {error && <p className="text-xs text-destructive">{error}</p>}
        <JobInterviewPrepModal job={job} open={interviewModalOpen} onClose={() => setInterviewModalOpen(false)} />
        <JobResumeOptimizeModal job={job} open={optimizeModalOpen} onClose={() => setOptimizeModalOpen(false)} />
        <ApplyAssistantModal job={job} open={applyModalOpen} onClose={() => setApplyModalOpen(false)} onComplete={onApplyComplete} />
      </div>
    )
  }

  return (
    <div className={compact ? "space-y-2" : "space-y-3"}>
      <div className="flex flex-wrap gap-2">
        <Button type="button" size={compact ? "sm" : "default"} variant="outline" disabled={busy} onClick={onSave}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Bookmark className="size-4" />}
          Save Job
        </Button>
        <Button type="button" size={compact ? "sm" : "default"} variant="outline" disabled={busy} onClick={() => setInterviewModalOpen(true)}>
          <Mic className="size-4" />
          Prepare for Interview
        </Button>
        <Button type="button" size={compact ? "sm" : "default"} variant="outline" disabled={busy} onClick={() => setOptimizeModalOpen(true)}>
          <Sparkles className="size-4" />
          Optimize Resume
        </Button>
        {canAssistedApply && (
          <Button type="button" size={compact ? "sm" : "default"} variant="default" disabled={busy} onClick={() => setApplyModalOpen(true)}>
            <Bot className="size-4" />
            Assisted Apply
          </Button>
        )}
        <Button type="button" size={compact ? "sm" : "default"} variant="secondary" disabled={busy} onClick={onApply}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
          Mark Applied
        </Button>
      </div>
      {application && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-muted-foreground">Application:</span>
          <span className="font-medium">{getStatusLabel(application.status)}</span>
          <select
            value={application.status}
            onChange={(e) => onStatusChange(e.target.value)}
            disabled={busy}
            className="h-8 rounded-md border border-input bg-background px-2 text-xs"
          >
            {APPLICATION_STATUSES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      )}
      {error && <p className="text-xs text-destructive">{error}</p>}
      <JobInterviewPrepModal job={job} open={interviewModalOpen} onClose={() => setInterviewModalOpen(false)} />
      <JobResumeOptimizeModal job={job} open={optimizeModalOpen} onClose={() => setOptimizeModalOpen(false)} />
      <ApplyAssistantModal job={job} open={applyModalOpen} onClose={() => setApplyModalOpen(false)} onComplete={onApplyComplete} />
    </div>
  )
}
