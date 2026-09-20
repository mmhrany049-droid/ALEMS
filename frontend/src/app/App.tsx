/**
 * App — providers + router.
 * doc 07.4: Framer Motion اجباری (MotionConfig reducedMotion="user" → NFR-5).
 * doc 07.5: Today / Study / Tests / Review / Plan / Exams / Progress / Settings
 * Phase 1: auth guardها — /auth (standalone)، /onboarding + /* (RequireAuth).
 */
import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { ThemeProvider } from './theme'
import { AuthProvider, useAuth } from './auth'
import { Layout } from './layout'
import { Spinner } from '../components/Spinner'
import { AuthPage } from '../features/auth/AuthPage'
import { OnboardingPage } from '../features/onboarding/OnboardingPage'
import { TodayPage } from '../features/today/TodayPage'
import { StudyPage } from '../features/study/StudyPage'
import { TestsPage } from '../features/tests/TestsPage'
import { ReviewPage } from '../features/review/ReviewPage'
import { PlanPage } from '../features/plan/PlanPage'
import { ExamsPage } from '../features/exams/ExamsPage'
import { ProgressPage } from '../features/progress/ProgressPage'
import { SettingsPage } from '../features/settings/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function Splash() {
  return (
    <div className="flex min-h-full items-center justify-center bg-bg">
      <div className="flex flex-col items-center gap-3 text-muted">
        <Spinner size={26} />
        <span className="text-body-sm">در حال آماده‌سازی ALEMS…</span>
      </div>
    </div>
  )
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Navigate to="/auth" replace />
  return <>{children}</>
}

function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (user) return <Navigate to="/" replace />
  return <>{children}</>
}

function NotFound() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-20 text-center text-muted">
      صفحه پیدا نشد.
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <MotionConfig reducedMotion="user">
          <BrowserRouter>
            <AuthProvider>
              <Routes>
                <Route
                  path="/auth"
                  element={
                    <GuestOnly>
                      <AuthPage />
                    </GuestOnly>
                  }
                />
                <Route
                  path="/onboarding"
                  element={
                    <RequireAuth>
                      <Layout>
                        <OnboardingPage key="onboarding" />
                      </Layout>
                    </RequireAuth>
                  }
                />
                <Route
                  path="/"
                  element={
                    <RequireAuth>
                      <Layout>
                        <Routes>
                          <Route index element={<TodayPage key="today" />} />
                          <Route path="study" element={<StudyPage key="study" />} />
                          <Route path="tests" element={<TestsPage key="tests" />} />
                          <Route path="review" element={<ReviewPage key="review" />} />
                          <Route path="plan" element={<PlanPage key="plan" />} />
                          <Route path="exams" element={<ExamsPage key="exams" />} />
                          <Route path="progress" element={<ProgressPage key="progress" />} />
                          <Route path="settings" element={<SettingsPage key="settings" />} />
                          <Route path="*" element={<NotFound />} />
                        </Routes>
                      </Layout>
                    </RequireAuth>
                  }
                />
              </Routes>
            </AuthProvider>
          </BrowserRouter>
        </MotionConfig>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
