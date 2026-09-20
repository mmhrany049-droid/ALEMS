/**
 * AuthProvider — session state (phase 1).
 * - boot: token موجود → GET /auth/me (نسخه‌ی منقضی خودکار پاک می‌شود)
 * - register/login → token در memory + localStorage
 * - logout → POST /auth/logout + پاک‌سازی هر دو
 */
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, ApiError } from '../lib/api'
import { clearToken, getStoredToken, storeToken } from '../lib/auth'
import type { AuthResponse, MeResponse, StudentProfile } from '../lib/schemas'

interface AuthCtx {
  user: { email: string; full_name: string | null; role: string } | null
  student: StudentProfile | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, full_name: string | null) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthCtx['user']>(null)
  const [student, setStudent] = useState<StudentProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const applyMe = useCallback((me: MeResponse) => {
    setUser({ email: me.user.email, full_name: me.user.full_name, role: me.user.role })
    setStudent(me.student)
  }, [])

  const refresh = useCallback(async () => {
    if (!getStoredToken()) {
      setUser(null)
      setStudent(null)
      return
    }
    try {
      applyMe(await api.get<MeResponse>('/auth/me'))
    } catch {
      clearToken()
      setUser(null)
      setStudent(null)
    }
  }, [applyMe])

  useEffect(() => {
    refresh().finally(() => setLoading(false))
  }, [refresh])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post<AuthResponse>('/auth/login', { email, password })
    storeToken(res.access_token)
    applyMe({ user: res.user, student: res.student })
  }, [applyMe])

  const register = useCallback(async (email: string, password: string, full_name: string | null) => {
    const res = await api.post<AuthResponse>('/auth/register', { email, password, full_name })
    storeToken(res.access_token)
    applyMe({ user: res.user, student: res.student })
  }, [applyMe])

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout')
    } catch (e) {
      if (!(e instanceof ApiError) || e.status !== 401) {
        /* logout از سمت client ادامه پیدا می‌کند */
      }
    }
    clearToken()
    setUser(null)
    setStudent(null)
  }, [])

  return <Ctx.Provider value={{ user, student, loading, login, register, logout, refresh }}>{children}</Ctx.Provider>
}

export function useAuth() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
