import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { getAccessToken, getRefreshToken } from "@/lib/apiClient"
import { clearNewUserRegistration, markNewUserRegistration } from "@/lib/newUserOnboarding"
import { markTourPendingForLogin } from "@/lib/platformTour"
import * as authService from "@/services/authService"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadSession = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await authService.fetchMe()
      setUser(me)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  const login = useCallback(async (credentials) => {
    const data = await authService.login(credentials)
    clearNewUserRegistration()
    markTourPendingForLogin()
    setUser(data.user)
    return data
  }, [])

  const register = useCallback(async (payload) => {
    const data = await authService.register(payload)
    markNewUserRegistration()
    markTourPendingForLogin()
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(async () => {
    await authService.logout(getRefreshToken())
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
