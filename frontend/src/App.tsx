import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { Spinner } from './components/ui';
import { useAuth } from './hooks/useAuth';
import AuthPage from './features/auth/AuthPage';
import OnboardingPage from './features/onboarding/OnboardingPage';
import TodayPage from './features/today/TodayPage';
import StudyPage from './features/study/StudyPage';
import TestsPage from './features/tests/TestsPage';
import ReviewPage from './features/review/ReviewPage';
import PlanningPage from './features/planning/PlanningPage';
import ExamsPage from './features/exams/ExamsPage';
import ExamRunPage from './features/exams/ExamRunPage';
import AnalyticsPage from './features/analytics/AnalyticsPage';
import SettingsPage from './features/settings/SettingsPage';

export default function App() {
  const { user, profile, loading } = useAuth();

  if (loading) {
    return <Spinner label="در حال آماده‌سازی ALEMS..." />;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="*" element={<Navigate to="/auth" replace />} />
      </Routes>
    );
  }

  // سند 8.6: کاربر بدون پروفایل کامل → هدایت به تکمیل پروفایل قبل از بخش‌های اصلی
  if (profile && !profile.is_complete) {
    return (
      <Routes>
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="*" element={<Navigate to="/onboarding" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/today" element={<TodayPage />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/tests" element={<TestsPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/planning" element={<PlanningPage />} />
        <Route path="/exams" element={<ExamsPage />} />
        <Route path="/exams/:examId/run" element={<ExamRunPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/today" replace />} />
      </Route>
    </Routes>
  );
}
