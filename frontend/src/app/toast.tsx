/**
 * Toast — بازخورد غیرمزاحم (doc 07.9، فاز ۸).
 * پایین-مرکز (بالای bottom nav)، حداکثر ۳ هم‌زمان، auto-dismiss:
 * موفقیت/اطلاع ~۴s، خطا ~۶s (خطای فارسی قابل اقدام باید خوانده شود).
 * Motion: ورود fade+slide با EASE_OUT؛ خروج سریع (doc 07.4).
 */
import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Icon } from '../components/Icon'
import { D, EASE_OUT } from '../motion/variants'

type ToastKind = 'success' | 'error' | 'info'

interface ToastItem {
  id: number
  kind: ToastKind
  text: string
}

export interface ToastApi {
  toast: (kind: ToastKind, text: string) => void
  success: (text: string) => void
  error: (text: string) => void
  info: (text: string) => void
}

const ToastCtx = createContext<ToastApi | null>(null)

export function useToast(): ToastApi {
  const ctx = useContext(ToastCtx)
  if (!ctx) throw new Error('useToast باید داخل ToastProvider استفاده شود.')
  return ctx
}

const KIND_STYLE: Record<ToastKind, string> = {
  success: 'bg-success text-white',
  error: 'bg-danger text-white',
  info: 'border border-border bg-surface text-ink shadow-soft',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const nextId = useRef(1)

  const toast = useCallback((kind: ToastKind, text: string) => {
    const id = nextId.current++
    setItems((cur) => [...cur, { id, kind, text }].slice(-3))
    const ttl = kind === 'error' ? 6000 : 3800
    window.setTimeout(() => setItems((cur) => cur.filter((t) => t.id !== id)), ttl)
  }, [])

  const api = useMemo<ToastApi>(
    () => ({
      toast,
      success: (text) => toast('success', text),
      error: (text) => toast('error', text),
      info: (text) => toast('info', text),
    }),
    [toast],
  )

  const dismiss = (id: number) => setItems((cur) => cur.filter((t) => t.id !== id))

  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-20 z-[60] flex flex-col items-center gap-2 px-4 md:bottom-6"
        role="status"
        aria-live="polite"
      >
        <AnimatePresence initial={false}>
          {items.map((t) => (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 16, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.97, transition: { duration: D.fast } }}
              transition={{ duration: D.normal, ease: EASE_OUT }}
              className={['pointer-events-auto flex max-w-md items-center gap-2 rounded-lg px-4 py-2.5 text-body-sm font-semibold', KIND_STYLE[t.kind]].join(' ')}
            >
              <Icon name={t.kind === 'success' ? 'check' : t.kind === 'error' ? 'alert' : 'sparkle'} size={16} />
              <span className="min-w-0 flex-1 leading-6">{t.text}</span>
              <button
                type="button"
                onClick={() => dismiss(t.id)}
                aria-label="بستن"
                className="shrink-0 rounded-md px-1 text-[13px] opacity-70 hover:opacity-100"
              >
                ✕
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}
