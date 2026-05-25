import { FileText } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useResumeOnboarding } from "@/context/ResumeOnboardingContext"

export function ResumeOnboardingModal({ onNavigate }) {
  const { showModal, acknowledgeResumeRequired } = useResumeOnboarding()

  if (!showModal) return null

  const handleOk = () => {
    acknowledgeResumeRequired()
    onNavigate("resume-hub")
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resume-onboarding-title"
      className="fixed inset-0 z-[220] flex items-end justify-center bg-black/60 p-4 backdrop-blur-sm sm:items-center"
    >
      <div className="neon-glass w-full max-w-md rounded-2xl p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30">
            <FileText className="size-5" />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-indigo-300">
              Personalize Career OS
            </p>
            <h2 id="resume-onboarding-title" className="text-lg font-semibold tracking-tight">
              Your resume powers everything
            </h2>
          </div>
        </div>

        <p className="text-sm leading-relaxed text-muted-foreground">
          We need your resume to customize job matches, scan results, ATS insights, and AI
          recommendations to your background and goals.
        </p>

        <div className="mt-6 flex justify-end">
          <Button type="button" onClick={handleOk}>
            OK
          </Button>
        </div>
      </div>
    </div>
  )
}
