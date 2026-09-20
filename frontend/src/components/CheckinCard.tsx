/**
 * CheckinCard — check-in روزانه (doc 13 §13.6: energy/focus/motivation/stress/fatigue, 1..5).
 * - full: onboarding step 2
 * - compact: Today Hub — اگر امروز check-in شده، وضعیت را نشان می‌دهد + «ویرایش»
 * upsert سمت backend (دو بار در یک روز ≠ duplicate).
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { api, ApiError } from '../lib/api'
import type { CheckinDims, StateOut } from '../lib/schemas'
import { faDigits } from '../lib/dates'
import { Card } from './Card'
import { D, EASE_OUT } from '../motion/variants'

export const DIMS: { key: keyof CheckinDims; label: string; positive: boolean }[] = [
  { key: 'energy', label: 'انرژی', positive: true },
  { key: 'focus', label: 'تمرکز', positive: true },
  { key: 'motivation', label: 'انگیزه', positive: true },
  { key: 'stress', label: 'استرس', positive: false },
  { key: 'fatigue', label: 'خستگی', positive: false },
]

const DEFAULTS: CheckinDims = { energy: 3, focus: 3, motivation: 3, stress: 2, fatigue: 2 }

export function CheckinCard({ state, onSaved }: { state: StateOut | null; onSaved?: (s: StateOut) => void }) {
  const [editing, setEditing] = useState(!state?.today)
  const [vals, setVals] = useState<CheckinDims>(state?.today ?? state?.last ?? DEFAULTS)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const submit = async () => {
    setError(null)
    setBusy(true)
    try {
      const res = await api.post<StateOut>('/students/me/checkin', vals)
      onSaved?.(res)
      setEditing(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 1600)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'ثبت نشد؛ دوباره تلاش کن.')
    } finally {
      setBusy(false)
    }
  }

  const today = state?.today
  return (
    <Card className="flex h-full flex-col gap-3 p-4 md:p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-title-sm font-bold">حالت امروز</h2>
        <div className="flex items-center gap-2">
          {saved && (
            <motion.span
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: [0.5, 1.15, 1], opacity: 1 }}
              transition={{ duration: D.slow, ease: EASE_OUT }}
              className="flex items-center gap-1 text-body-sm font-semibold text-success"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M4 12.5 9.5 18 20 6.5" />
              </svg>
              ثبت شد
            </motion.span>
          )}
          {!editing && (
            <button onClick={() => setEditing(true)} className="text-body-sm font-semibold text-primary hover:opacity-80">
              {today ? 'ویرایش' : 'ثبت امروز'}
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="flex flex-col gap-3">
          {DIMS.map((d) => (
            <div key={String(d.key)} className="flex items-center justify-between gap-3">
              <span className="w-16 text-body-sm">{d.label}</span>
              <div className="flex flex-1 items-center justify-end gap-1.5" role="radiogroup" aria-label={d.label}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    role="radio"
                    aria-checked={vals[d.key] === n}
                    onClick={() => setVals((v) => ({ ...v, [d.key]: n }))}
                    className={[
                      'h-9 w-9 rounded-full border text-body-sm font-bold transition-all',
                      vals[d.key] === n
                        ? d.positive
                          ? 'scale-105 border-primary bg-primary text-white'
                          : 'scale-105 border-warning bg-warning text-white'
                        : 'border-border bg-surface text-muted hover:border-primary/50',
                    ].join(' ')}
                  >
                    {faDigits(n)}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{error}</p>}
          <div className="mt-1 flex justify-end">
            <motion.button
              whileTap={{ scale: 0.98 }}
              transition={{ duration: D.fast }}
              onClick={submit}
              disabled={busy}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-body-sm font-semibold text-white shadow-soft transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {busy ? 'در حال ثبت…' : today ? 'به‌روزرسانی' : 'ثبت check-in'}
            </motion.button>
          </div>
        </div>
      ) : today ? (
        <div>
          <div className="grid grid-cols-5 gap-2">
            {DIMS.map((d) => (
              <div key={String(d.key)} className="flex flex-col items-center gap-1 rounded-md bg-surface-2 py-2.5">
                <span className="text-title-sm font-bold">{faDigits(String(today[d.key]))}</span>
                <span className="text-body-sm text-muted">{d.label}</span>
                <div className="h-1 w-8 overflow-hidden rounded-full bg-border">
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: today[d.key] / 5 }}
                    transition={{ duration: D.slow, ease: EASE_OUT }}
                    className={`h-full origin-right ${d.positive ? 'bg-primary' : 'bg-warning'}`}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-body-sm text-muted">
            check-in امروز: {today.date_jalali} · داده‌های check-in: {faDigits(state!.data_days)} روز
          </p>
        </div>
      ) : (
        <p className="rounded-md bg-surface-2 px-3 py-2 text-body-sm text-muted">
          هنوز برای امروز check-in نکرده‌ای — حالتت را بگو تا برنامه‌ی روز واقع‌بینانه‌تر شود.
        </p>
      )}
    </Card>
  )
}
