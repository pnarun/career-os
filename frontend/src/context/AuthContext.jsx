import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { AUTH_SESSION_EXPIRED_EVENT, getRefreshToken } from "@/lib/apiClient"
import {
  clearSessionBootstrap,
  resolveSession,
  setSessionBootstrapUser,
} from "@/lib/authSessionBootstrap"
import { clearNewUserRegistration, markNewUserRegistration } from "@/lib/newUserOnboarding"
import { markTourPendingForLogin } from "@/lib/platformTour"
import * as authService from "@/services/authService"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadSession = useCallback(async () => {
    const me = await resolveSession()
    setUser(me)
    setLoading(false)
  }, [])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  useEffect(() => {
    const onSessionExpired = () => {
      clearSessionBootstrap()
      setUser(null)
      setLoading(false)
    }
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, onSessionExpired)
    return () => window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, onSessionExpired)
  }, [])

  const login = useCallback(async (credentials) => {
    const data = await authService.login(credentials)
    clearNewUserRegistration()
    markTourPendingForLogin()
    setSessionBootstrapUser(data.user)
    setUser(data.user)
    return data
  }, [])

  const register = useCallback(async (payload) => {
    const data = await authService.register(payload)
    markNewUserRegistration()
    markTourPendingForLogin()
    setSessionBootstrapUser(data.user)
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(async () => {
    await authService.logout(getRefreshToken())
    clearSessionBootstrap()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser: loadSession,
    }),
    [user, loading, login, register, logout, loadSession]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
