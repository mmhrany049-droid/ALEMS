/**
 * Shell — doc 07.5:
 *  Desktop: sidebar باریک + content
 *  Mobile:  bottom nav با ۵ آیتم اصلی + more
 * Sections: Today, Study, Tests, Review, Plan, Exams, Progress, Settings
 */
import { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Icon, type IconName } from '../components/Icon'
import { useTheme } from './theme'
import { useAuth } from './auth'
import { todayJalali, formatJalaliLong, weekdayFa } from '../lib/dates'
import { BackendStatus } from './BackendStatus'
import { D, modal, backdrop } from '../motion/variants'

const NAV: { to: string; label: string; icon: IconName; main?: boolean }[] = [
  { to: '/', label: 'امروز', icon: 'home', main: true },
  { to: '/study', label: 'مطالعه', icon: 'book', main: true },
  { to: '/tests', label: 'تست‌ها', icon: 'test', main: true },
  { to: '/review', label: 'مرور', icon: 'review', main: true },
  { to: '/plan', label: 'برنامه', icon: 'plan', main: true },
  { to: '/exams', label: 'آزمون‌ها', icon: 'exam' },
  { to: '/progress', label: 'پیشرفت', icon: 'progress' },
  { to: '/import', label: 'وارد کردن کتاب', icon: 'book-open' },
  { to: '/settings', label: 'تنظیمات', icon: 'settings' },
]

function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return (
    <motion.button
      whileTap={{ scale: 0.92 }}
      transition={{ duration: D.fast }}
      onClick={toggle}
      aria-label={theme === 'dark' ? 'حالت روشن' : 'حالت تاریک'}
      className="flex h-10 w-10 items-center justify-center rounded-md border border-border bg-surface text-muted hover:text-ink"
    >
      <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={18} />
    </motion.button>
  )
}

function UserChip() {
  const { user } = useAuth()
  const navigate = useNavigate()
  if (!user) return null
  const initials = (user.full_name || user.email || '?')
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
  return (
    <motion.button
      whileTap={{ scale: 0.92 }}
      transition={{ duration: D.fast }}
      onClick={() => navigate('/settings')}
      aria-label="حساب کاربری"
      title={user.full_name || user.email}
      className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-body font-bold text-white"
    >
      {initials}
    </motion.button>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-white">
        <svg width="18" height="18" viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <path d="M9 22 16 9l7 13" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div>
        <div className="text-title-sm font-bold leading-none">ALEMS</div>
        <div className="mt-1 text-body-sm text-muted leading-none">نسخه ۲.</div>
      </div>
    </div>
  )
}

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const t = todayJalali()
  const [moreOpen, setMoreOpen] = useState(false)
  const moreItems = NAV.filter((n) => !n.main)
  const moreActive = moreItems.some((m) => (m.to === '/' ? location.pathname === '/' : location.pathname.startsWith(m.to)))

  return (
    <div className="flex h-full">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:gap-1 md:border-l md:border-border md:bg-surface md:p-4">
        <div className="mb-5 mt-1 px-2">
          <Brand />
        </div>
        <nav className="flex flex-1 flex-col gap-1" aria-label="ناوبری اصلی">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 rounded-md px-3 py-2.5 text-body-sm font-medium transition-colors',
                  isActive ? 'bg-primary-soft text-primary' : 'text-muted hover:bg-surface-2 hover:text-ink',
                ].join(' ')
              }
            >
              <Icon name={item.icon} size={19} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center justify-between rounded-md bg-surface-2 px-3 py-2.5">
          <div className="text-body-sm text-muted">
            <div className="font-semibold text-ink">{formatJalaliLong(t)}</div>
            <div className="text-body-sm">{weekdayFa(t)}</div>
          </div>
          <BackendStatus compact />
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header (mobile + desktop) */}
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border bg-surface/90 px-4 py-3 backdrop-blur md:px-5">
          <div className="md:hidden">
            <Brand />
          </div>
          <div className="hidden text-body-sm text-muted md:block">
            {weekdayFa(t)}، {formatJalaliLong(t)}
          </div>
          <div className="flex items-center gap-2">
            <UserChip />
            <BackendStatus />
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">{children}</AnimatePresence>
        </main>
      </div>

      {/* Mobile bottom nav — 5 اصلی + more (doc 07.5) */}
      <nav
        className="fixed inset-x-0 bottom-0 z-20 flex items-center justify-around border-t border-border bg-surface/95 px-1 py-1.5 backdrop-blur md:hidden"
        aria-label="ناوبری موبایل"
      >
        {NAV.filter((n) => n.main).map((item) => (
          <MobileNavBtn key={item.to} item={item} current={location.pathname} />
        ))}
        <button
          onClick={() => setMoreOpen(true)}
          className={[
            'flex flex-col items-center gap-0.5 rounded-md px-2 py-1 text-body-sm',
            moreActive ? 'text-primary' : 'text-muted',
          ].join(' ')}
          aria-label="بیشتر"
        >
          <Icon name="more" size={20} />
          <span>بیشتر</span>
        </button>
      </nav>

      {/* More sheet — modal pattern (doc 07.4 #6: scale + fade) */}
      <AnimatePresence>
        {moreOpen && (
          <>
            <motion.div
              key="backdrop"
              variants={backdrop}
              initial="initial"
              animate="animate"
              exit="exit"
              onClick={() => setMoreOpen(false)}
              className="fixed inset-0 z-30 bg-black/40"
            />
            <motion.div
              key="sheet"
              variants={modal}
              initial="initial"
              animate="animate"
              exit="exit"
              role="dialog"
              aria-label="بیشتر"
              className="fixed inset-x-3 bottom-20 z-40 rounded-lg border border-border bg-surface p-2 shadow-soft"
            >
              <div className="grid grid-cols-3 gap-1">
                {moreItems.map((m) => (
                  <NavLink
                    key={m.to}
                    to={m.to}
                    onClick={() => setMoreOpen(false)}
                    className="flex flex-col items-center gap-1 rounded-md px-2 py-3 text-body-sm text-muted hover:bg-surface-2"
                  >
                    <Icon name={m.icon} size={20} />
                    <span>{m.label}</span>
                  </NavLink>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

function MobileNavBtn({ item, current }: { item: { to: string; label: string; icon: IconName }; current: string }) {
  const active = item.to === '/' ? current === '/' : current.startsWith(item.to)
  return (
    <NavLink
      to={item.to}
      end={item.to === '/'}
      className={[
        'flex flex-col items-center gap-0.5 rounded-md px-2 py-1 text-body-sm',
        active ? 'text-primary' : 'text-muted',
      ].join(' ')}
    >
      <Icon name={item.icon} size={20} />
      <span>{item.label}</span>
    </NavLink>
  )
}
