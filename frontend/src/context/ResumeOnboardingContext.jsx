import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { useAuth } from "@/context/AuthContext"
import {
  clearNewUserRegistration,
  clearResumeGateSkipped,
  isNewUserRegistration,
} from "@/lib/newUserOnboarding"
import { shouldShowPlatformTour } from "@/lib/platformTour"
import { listResumes } from "@/services/preferencesService"

const ResumeOnboardingContext = createContext(null)

export function ResumeOnboardingProvider({ children }) {
  const { user, isAuthenticated } = useAuth()
  const userId = user?.id

  const [hasResume, setHasResume] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [resumeGateEnforced, setResumeGateEnforced] = useState(false)

  const refreshResumes = useCallback(async () => {
    if (!userId) {
      setHasResume(false)
      return false
    }
    try {
      const list = await listResumes()
      const has = Array.isArray(list) && list.length > 0
      setHasResume(has)
      if (has) {
        clearNewUserRegistration()
        clearResumeGateSkipped(userId)
        setResumeGateEnforced(false)
        setShowModal(false)
      }
      return has
    } catch {
      return false
    }
  }, [userId])

  useEffect(() => {
    if (!isAuthenticated || !userId) {
      setHasResume(false)
      setLoading(false)
      setShowModal(false)
      setResumeGateEnforced(false)
      return
    }

    setLoading(true)
    refreshResumes().finally(() => setLoading(false))
  }, [isAuthenticated, userId, refreshResumes])

  const isNewUserFlow = isNewUserRegistration()
  const gateActive = isNewUserFlow && !hasResume && resumeGateEnforced

  const notifyTourClosed = useCallback(() => {
    if (!userId || hasResume || !isNewUserRegistration()) {
      return
    }
    setShowModal(true)
  }, [userId, hasResume])

  useEffect(() => {
    if (loading || !userId || hasResume || !isNewUserFlow || showModal || resumeGateEnforced) return
    if (shouldShowPlatformTour(userId)) return
    setShowModal(true)
  }, [loading, userId, hasResume, isNewUserFlow, showModal, resumeGateEnforced])

  const acknowledgeResumeRequired = useCallback(() => {
    setResumeGateEnforced(true)
    setShowModal(false)
  }, [])

  const completeUpload = useCallback(() => {
    setHasResume(true)
    setResumeGateEnforced(false)
    clearNewUserRegistration()
    if (userId) clearResumeGateSkipped(userId)
    setShowModal(false)
  }, [userId])

  const isPageAllowed = useCallback(
    (page) => {
      if (!gateActive) return true
      return page === "resume-hub"
    },
    [gateActive]
  )

  const value = useMemo(
    () => ({
      loading,
      hasResume,
      gateActive,
      showModal,
      isNewUserFlow,
      refreshResumes,
      notifyTourClosed,
      acknowledgeResumeRequired,
      completeUpload,
      isPageAllowed,
    }),
    [
      loading,
      hasResume,
      gateActive,
      showModal,
      isNewUserFlow,
      refreshResumes,
      notifyTourClosed,
      acknowledgeResumeRequired,
      completeUpload,
      isPageAllowed,
    ]
  )

  return (
    <ResumeOnboardingContext.Provider value={value}>{children}</ResumeOnboardingContext.Provider>
  )
}

export function useResumeOnboarding() {
  const ctx = useContext(ResumeOnboardingContext)
  if (!ctx) {
    throw new Error("useResumeOnboarding must be used within ResumeOnboardingProvider")
  }
  return ctx
}
