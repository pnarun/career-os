import { FileText } from "lucide-react"

import { TopCenterDialog } from "@/components/ui/TopCenterDialog"
import { Button } from "@/components/ui/button"
import { useResumeOnboarding } from "@/context/ResumeOnboardingContext"

export function ResumeOnboardingModal({ onNavigate }) {
  const { showModal, acknowledgeResumeRequired } = useResumeOnboarding()

  const handleOk = () => {
    acknowledgeResumeRequired()
    onNavigate?.("resume-hub")
  }

  return (
    <TopCenterDialog
      open={showModal}
      onClose={handleOk}
      size="md"
      placement="top"
      backdrop="glass"
      aria-labelledby="resume-onboarding-title"
      title={
        <span className="flex items-center gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
            <FileText className="size-5" />
          </span>
          <span>
            <span className="block text-xs font-medium uppercase tracking-wide text-indigo-300">
              Personalize Career OS
            </span>
            <span id="resume-onboarding-title" className="block text-lg font-semibold">
              Your resume powers everything
            </span>
          </span>
        </span>
      }
      footer={
        <Button type="button" onClick={handleOk}>
          OK
        </Button>
      }
    >
      <p className="text-sm leading-relaxed text-muted-foreground">
        We need your resume to customize job matches, scan results, ATS insights, and AI
        recommendations to your background and goals.
      </p>
    </TopCenterDialog>
  )
}
