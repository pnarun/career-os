import { FileText, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useResumeOnboarding } from "@/context/ResumeOnboardingContext"

export function ResumeOnboardingModal({ onNavigate }) {
  const { showModal, skipGate, dismissModalForUpload } = useResumeOnboarding()

  if (!showModal) return null

  const handleUpload = () => {
    dismissModalForUpload()
    onNavigate("resume")
  }

  const handleSkip = () => {
    skipGate()
    onNavigate("resume")
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resume-onboarding-title"
      className="fixed inset-0 z-[220] flex items-end justify-center bg-black/60 p-4 backdrop-blur-sm sm:items-center"
    >
      <div className="neon-glass w-full max-w-md rounded-2xl p-6 shadow-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30">
              <FileText className="size-5" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-indigo-300">
                Get started
              </p>
              <h2 id="resume-onboarding-title" className="text-lg font-semibold tracking-tight">
                Upload your resume
              </h2>
            </div>
          </div>
          <button
            type="button"
            aria-label="Skip for now"
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            onClick={handleSkip}
          >
            <X className="size-5" />
          </button>
        </div>

        <p className="text-sm leading-relaxed text-muted-foreground">
          Sharing your resume helps us customize job matches, scan results, and AI recommendations
          for your background and goals.
        </p>

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="ghost" onClick={handleSkip}>
            Skip for now
          </Button>
          <Button type="button" onClick={handleUpload}>
            Upload resume
          </Button>
        </div>
      </div>
    </div>
  )
}
