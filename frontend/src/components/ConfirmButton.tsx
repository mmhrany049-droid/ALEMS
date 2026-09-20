/**
 * ConfirmButton — تأیید دومرحله‌ای برای عملیات مخرب (doc 07.9، فاز ۸).
 * کلیک اول →武装 (سوال تأیید + لغو کنار هم)؛ کلیک دوم → اجرا.
 * بعد از resetMs بدون اقدام، خودکار به حالت اول برمی‌گردد.
 */
import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { D, EASE_OUT } from '../motion/variants'

interface Props {
  onConfirm: () => void
  label?: string
  confirmLabel?: string
  cancelLabel?: string
  busy?: boolean
  disabled?: boolean
  resetMs?: number
  className?: string
}

export function ConfirmButton({
  onConfirm,
  label = 'حذف',
  confirmLabel = 'مطمئنی؟',
  cancelLabel = 'بی‌خیال',
  busy = false,
  disabled = false,
  resetMs = 3500,
  className = '',
}: Props) {
  const [armed, setArmed] = useState(false)
  const timer = useRef<number | null>(null)

  useEffect(() => {
    if (armed) {
      timer.current = window.setTimeout(() => setArmed(false), resetMs)
      return () => {
        if (timer.current) window.clearTimeout(timer.current)
      }
    }
  }, [armed, resetMs])

  if (!armed) {
    return (
      <motion.button
        type="button"
        whileTap={disabled ? undefined : { scale: 0.96 }}
        transition={{ duration: D.fast }}
        onClick={() => setArmed(true)}
        disabled={disabled}
        className={[
          'inline-flex items-center gap-1.5 rounded-md bg-danger-soft px-3 py-1.5 text-body-sm font-semibold text-danger',
          'transition-opacity hover:opacity-90 disabled:opacity-50',
          className,
        ].join(' ')}
      >
        {label}
      </motion.button>
    )
  }

  return (
    <span className={['inline-flex items-center gap-1.5', className].join(' ')}>
      <AnimatePresence initial={false}>
        <motion.span
          key="confirm-group"
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1, transition: { duration: D.fast, ease: EASE_OUT } }}
          className="inline-flex items-center gap-1.5"
        >
          <span className="text-body-sm font-medium text-muted">{confirmLabel}</span>
          <motion.button
            type="button"
            whileTap={{ scale: 0.96 }}
            transition={{ duration: D.fast }}
            onClick={() => {
              setArmed(false)
              onConfirm()
            }}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-md bg-danger px-3 py-1.5 text-body-sm font-bold text-white disabled:opacity-50"
          >
            {busy ? '…' : label}
          </motion.button>
          <button
            type="button"
            onClick={() => setArmed(false)}
            className="rounded-md border border-border px-2.5 py-1.5 text-body-sm text-muted hover:bg-surface-2"
          >
            {cancelLabel}
          </button>
        </motion.span>
      </AnimatePresence>
    </span>
  )
}
