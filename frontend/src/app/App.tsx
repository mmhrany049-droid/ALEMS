/**
 * App — providers + router.
 * doc 07.4: Framer Motion اجباری (MotionConfig reducedMotion="user" → NFR-5).
 * doc 07.5: Today / Study / Tests / Review / Plan / Exams / Progress / Settings
 * Phase 1: auth guardها — /auth (standalone)، /onboarding + /* (RequireAuth).
 *
 * ساختار route (ریشه‌ای اصلاح‌شده): صفحات اصلی «فرزند» route واحد «/» هستند و با
 * <Outlet/> رندر می‌شوند — نه <Routes> تودرتو زیر route بدون splat (که باعث
 * «No routes matched /study» و صفحه سفید می‌شد).
 * GuestOnly: بعد از ورود، مقصد بر اساس کامل بودن پروفایل انتخاب می‌شود
 * (ثبت‌نام → onboarding بدون flash خوردن صفحه Today).
 */
import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { ThemeProvider } from './theme'
import { ToastProvider } from './toast'
import { ErrorBoundary } from './ErrorBoundary'
import { AuthProvider, useAuth } from './auth'
import { Layout } from './layout'
import { Spinner } from '../components/Spinner'
import { AuthPage } from '../features/auth/AuthPage'
import { OnboardingPage } from '../features/onboarding/OnboardingPage'
import { TodayPage } from '../features/today/TodayPage'
import { StudyPage } from '../features/study/StudyPage'
import { ImportPage } from '../features/import/ImportPage'
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
  const { user, student, loading } = useAuth()
  if (loading) return <Splash />
  // پروفایل ناقص → onboarding؛ کامل → Today. (بدون mount شدن لحظه‌ای Today و
  // درخواست‌های هدررفته بین register و navigate — اصلاح ریشه‌ای flash ورود.)
  if (user) return <Navigate to={student?.grade ? '/' : '/onboarding'} replace />
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
          <ToastProvider>
            <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
              <ErrorBoundary title="خطای غیرمنتظره در ALEMS">
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
                            <Outlet />
                          </Layout>
                        </RequireAuth>
                      }
                    >
                      <Route index element={<TodayPage key="today" />} />
                      <Route path="study" element={<StudyPage key="study" />} />
                      <Route path="import" element={<ImportPage key="import" />} />
                      <Route path="tests" element={<TestsPage key="tests" />} />
                      <Route path="review" element={<ReviewPage key="review" />} />
                      <Route path="plan" element={<PlanPage key="plan" />} />
                      <Route path="exams" element={<ExamsPage key="exams" />} />
                      <Route path="progress" element={<ProgressPage key="progress" />} />
                      <Route path="settings" element={<SettingsPage key="settings" />} />
                      <Route path="*" element={<NotFound />} />
                    </Route>
                  </Routes>
                </AuthProvider>
              </ErrorBoundary>
            </BrowserRouter>
          </ToastProvider>
        </MotionConfig>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
