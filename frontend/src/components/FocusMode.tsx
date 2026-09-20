/**
 * FocusMode — حالت تمرکز (doc 07.7، فاز ۸):
 * - مخفی کردن ناوبری: overlay تمام‌صفحه z-[70] روی sidebar/bottom-nav/header
 * - فقط تایمر + سوالات/کار جاری (children)
 * - خروج تأییدشده: دکمه خروج → «خروج از حالت تمرکز؟» (بله/بمان)؛ Escape هم تأیید می‌خواهد
 */
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Icon } from './Icon'
import { faDigits } from '../lib/dates'
import { D, EASE_OUT, fade } from '../motion/variants'

function fmt(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

interface Props {
  title: string
  subtitle?: string
  /** اگر داده شود، شمارش معکوس «باقی‌مانده» هم نشان داده می‌شود (دقیقه). */
  minutes?: number | null
  onExit: () => void
  children: ReactNode
}

export function FocusMode({ title, subtitle, minutes, onExit, children }: Props) {
  const [elapsed, setElapsed] = useState(0)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    const t = window.setInterval(() => setElapsed((e) => e + 1), 1000)
    return () => window.clearInterval(t)
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setConfirming(true)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // قفل اسکرول بدنه پشت overlay
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [])

  const remaining = minutes && minutes > 0 ? Math.max(0, minutes * 60 - elapsed) : null

  return (
    <motion.div
      variants={fade}
      initial="initial"
      animate="animate"
      exit="exit"
      className="fixed inset-0 z-[70] flex flex-col bg-bg"
      role="dialog"
      aria-modal="true"
      aria-label="حالت تمرکز"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-3 md:px-8">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-soft text-primary">
              <Icon name="focus" size={17} />
            </span>
            <h2 className="truncate text-title-sm font-bold">{title}</h2>
            <span className="shrink-0 rounded-md bg-primary-soft px-2 py-0.5 text-[11px] font-bold text-primary">حالت تمرکز</span>
          </div>
          {subtitle && <p className="mt-1 truncate text-body-sm text-muted">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className={['text-title font-bold tabular-nums', remaining != null && remaining < 60 ? 'text-danger' : 'text-ink'].join(' ')}>
              {fmt(elapsed)}
            </div>
            <div className="text-[11px] text-muted">
              {remaining != null ? `باقی‌مانده ${faDigits(fmt(remaining))}` : 'زمان سپری‌شده'}
            </div>
          </div>

          {/* خروج تأییدشده (doc 07.7) */}
          {!confirming ? (
            <motion.button
              type="button"
              whileTap={{ scale: 0.96 }}
              transition={{ duration: D.fast }}
              onClick={() => setConfirming(true)}
              className="rounded-md border border-border px-3 py-2 text-body-sm font-semibold text-muted hover:text-ink"
            >
              خروج
            </motion.button>
          ) : (
            <AnimatePresence>
              <motion.span
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1, transition: { duration: D.fast, ease: EASE_OUT } }}
                className="flex items-center gap-1.5 rounded-md bg-warning-soft px-2.5 py-1.5"
              >
                <span className="text-body-sm font-medium text-warning">خروج از تمرکز؟</span>
                <button
                  type="button"
                  onClick={onExit}
                  className="rounded-md bg-danger px-2.5 py-1 text-body-sm font-bold text-white"
                >
                  خروج
                </button>
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  className="rounded-md border border-border bg-surface px-2.5 py-1 text-body-sm text-muted"
                >
                  بمان
                </button>
              </motion.span>
            </AnimatePresence>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 py-5 md:px-8">
        <div className="mx-auto max-w-3xl">{children}</div>
      </div>
    </motion.div>
  )
}
