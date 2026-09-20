/**
 * Tests — موتور تست (فاز ۳، doc 09 §9.2-9.4).
 * تب‌ها: آزمون جدید (range/parity + preview) · تاریخچه · نتایج قدیمی (past import
 * با not_entered) · دفترچه خطا. هنگام اجرای جلسه، تب‌ها مخفی می‌شوند (تمرکز).
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { SessionCreateOut } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { D, EASE_OUT } from '../../motion/variants'
import { SessionSetup } from './SessionSetup'
import { SessionRunner } from './SessionRunner'
import { HistoryTab } from './HistoryTab'
import { PastImportTab } from './PastImportTab'
import { ErrorNotebookTab } from './ErrorNotebookTab'

type Tab = 'new' | 'history' | 'past' | 'notes'

const TABS: { id: Tab; label: string }[] = [
  { id: 'new', label: 'آزمون جدید' },
  { id: 'history', label: 'تاریخچه' },
  { id: 'past', label: 'نتایج قدیمی' },
  { id: 'notes', label: 'دفترچه خطا' },
]

export function TestsPage() {
  const [tab, setTab] = useState<Tab>('new')
  const [active, setActive] = useState<SessionCreateOut | null>(null)

  return (
    <Page title="تست‌ها" subtitle="ثبت تست سریع، انتخاب بازه و زوج/فرد، نتایج قدیمی و دفترچه خطا">
      {active ? (
        <SessionRunner initial={active} onExit={() => setActive(null)} />
      ) : (
        <>
          <div className="mb-4 flex gap-1 overflow-x-auto rounded-lg border border-border bg-surface p-1" role="tablist" aria-label="بخش‌های تست">
            {TABS.map((t) => (
              <button
                key={t.id}
                role="tab"
                aria-selected={tab === t.id}
                onClick={() => setTab(t.id)}
                className={[
                  'relative shrink-0 rounded-md px-3.5 py-2 text-body-sm font-semibold transition-colors',
                  tab === t.id ? 'text-primary' : 'text-muted hover:text-ink',
                ].join(' ')}
              >
                {tab === t.id && (
                  <motion.span
                    layoutId="tests-tab"
                    className="absolute inset-0 rounded-md bg-primary-soft"
                    transition={{ duration: D.normal, ease: EASE_OUT }}
                  />
                )}
                <span className="relative">{t.label}</span>
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: D.fast, ease: EASE_OUT }}
            >
              {tab === 'new' && <SessionSetup onStart={setActive} />}
              {tab === 'history' && <HistoryTab onNew={() => setTab('new')} onResume={setActive} />}
              {tab === 'past' && <PastImportTab />}
              {tab === 'notes' && <ErrorNotebookTab />}
            </motion.div>
          </AnimatePresence>
        </>
      )}
    </Page>
  )
}
