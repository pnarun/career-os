import { X } from "lucide-react"

import { TopCenterDialog } from "@/components/ui/TopCenterDialog"
import { Button } from "@/components/ui/button"

export function JobDescriptionModal({ job, open, onClose }) {
  if (!job) return null

  const description =
    String(job.description || "").trim() ||
    `${job.title || "Role"} at ${job.company || "Company"}. Full description was not provided by the job source.`

  return (
    <TopCenterDialog
      open={open}
      onClose={onClose}
      title={job.title}
      description={job.company}
      aria-labelledby="job-description-title"
      footer={
        <Button type="button" variant="outline" onClick={onClose}>
          Close
        </Button>
      }
    >
      <p id="job-description-title" className="sr-only">
        Job description
      </p>
      <div className="max-h-[50vh] overflow-y-auto rounded-lg border border-border bg-muted/20 p-4 text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
        {description}
      </div>
      {job.location ? (
        <p className="mt-3 text-xs text-muted-foreground">Location: {job.location}</p>
      ) : null}
    </TopCenterDialog>
  )
}
