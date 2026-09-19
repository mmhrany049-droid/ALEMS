// چیدمان اصلی — ناوبری RTL (۷.۳)
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { faNumber, formatJalaliWithWeekday, todayISO } from '../lib/jalali';

const NAV = [
  { to: '/today', label: 'امروز', icon: '🌤' },
  { to: '/study', label: 'مطالعه', icon: '📚' },
  { to: '/tests', label: 'تست‌ها', icon: '✏️' },
  { to: '/review', label: 'مرور', icon: '🔁' },
  { to: '/planning', label: 'برنامه', icon: '🗓' },
  { to: '/exams', label: 'آزمون', icon: '🎯' },
  { to: '/analytics', label: 'تحلیل', icon: '📊' },
  { to: '/settings', label: 'تنظیمات', icon: '⚙️' },
];

export default function Layout() {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-xl bg-primary-600 text-white grid place-items-center font-bold">A</div>
            <div>
              <div className="font-bold text-slate-900 leading-tight">ALEMS</div>
              <div className="text-[11px] text-slate-400 leading-tight">
                {profile?.full_name ? `${profile.full_name} · ` : ''}
                {formatJalaliWithWeekday(todayISO())}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden md:inline text-xs text-slate-400">
              {user?.role === 'admin' ? 'مدیر سیستم' : 'دانش‌آموز'}
            </span>
            <button
              className="btn-secondary !py-1.5 text-xs"
              onClick={() => {
                logout();
                navigate('/auth');
              }}
            >
              خروج
            </button>
          </div>
        </div>
        <nav className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto pb-1 -mt-0.5" aria-label="منوی اصلی">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `shrink-0 flex items-center gap-1.5 rounded-t-xl px-3.5 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-semibold'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                }`
              }
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="text-center text-xs text-slate-400 py-4">
        ALEMS نسخه {faNumber('1.0.0')} — سامانه مدیریت زندگی تحصیلی و مسیر کنکور · داده‌ها متعلق به شماست
      </footer>
    </div>
  );
}
