/**
 * App — providers + router.
 * doc 07.4: Framer Motion اجباری (MotionConfig reducedMotion="user" → NFR-5).
 * doc 07.5: Today / Study / Tests / Review / Plan / Exams / Progress / Settings
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { ThemeProvider } from './theme'
import { Layout } from './layout'
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
            <Layout>
              <Routes>
                <Route path="/" element={<TodayPage key="today" />} />
                <Route path="/study" element={<StudyPage key="study" />} />
                <Route path="/tests" element={<TestsPage key="tests" />} />
                <Route path="/review" element={<ReviewPage key="review" />} />
                <Route path="/plan" element={<PlanPage key="plan" />} />
                <Route path="/exams" element={<ExamsPage key="exams" />} />
                <Route path="/progress" element={<ProgressPage key="progress" />} />
                <Route path="/settings" element={<SettingsPage key="settings" />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Layout>
          </BrowserRouter>
        </MotionConfig>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
