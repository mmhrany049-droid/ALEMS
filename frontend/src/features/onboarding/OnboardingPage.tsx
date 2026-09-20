/**
 * Onboarding — چندمرحله‌ای با Framer Motion (phase 1).
 * Steps: 1) خوش‌آمد 2) پروفایل (پایه/رشته/هدف) 3) check-in 4) تمید
 * هر step یک کارت انیمیشنی؛ پیشرفت با progress bar؛ back/forward.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from '../../app/auth'
import { api, ApiError } from '../../lib/api'
import type { StateOut } from '../../lib/schemas'
import { faDigits, formatJalaliLong, todayJalali } from '../../lib/dates'
import { CheckinCard } from '../../components/CheckinCard'
import { Spinner } from '../../components/Spinner'
import { D, EASE_OUT } from '../../motion/variants'

const GRADES = ['دوازدهم', 'یازدهم', 'دهم', 'دوم دبیرستان', 'اول دبیرستان']
const TRACKS = ['ریاضی', 'فیزیک', 'شیمی', 'زمین', 'تست و ریاضی', 'ادبیات و زبان', 'هنر']

export function OnboardingPage() {
  const { user, student, refresh } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [grade, setGrade] = useState(student?.grade ?? GRADES[0])
  const [track, setTrack] = useState(student?.track ?? TRACKS[0])
  const [target, setTarget] = useState(student?.target ?? '')
  const [profileSaving, setProfileSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [state, setState] = useState<StateOut | null>(null)

  const saveProfile = async () => {
    setProfileSaving(true)
    setError(null)
    try {
      await api.put('/students/me', { grade, track, target: target.trim() || null })
      await refresh()
      setStep(2)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'ذخیره نشد؛ دوباره تلاش کن.')
    } finally {
      setProfileSaving(false)
    }
  }

  const steps = [
    { title: 'خوش آمدی', hint: 'شروع می‌کنیم' },
    { title: 'پروفایل کنکوری', hint: 'پایه، رشته و هدف' },
    { title: 'حالت امروز', hint: 'check-in اولیه' },
    { title: 'تمام شد', hint: 'آماده‌ی شروع' },
  ]
  const s = steps[step]

  return (
    <div className="flex min-h-full flex-col bg-bg">
      {/* progress */}
      <div className="mx-auto w-full max-w-2xl px-4 pt-8">
        <div className="mb-2 flex items-center justify-between text-body-sm text-muted">
          <span className="font-semibold">{faDigits(step + 1)} از {faDigits(steps.length)} — {s.title}</span>
          <span>{s.hint}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
          <motion.div
            className="h-full origin-right rounded-full bg-primary"
            animate={{ width: `${((step + 1) / steps.length) * 100}%` }}
            transition={{ duration: D.normal, ease: EASE_OUT }}
          />
        </div>
      </div>

      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-4 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: -24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 24 }}
            transition={{ duration: D.normal, ease: EASE_OUT }}
            className="rounded-lg border border-border bg-surface p-6 shadow-soft md:p-8"
          >
            {step === 0 && (
              <div>
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                    <path d="M9 22 16 9l7 13" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h1 className="text-title-lg font-bold">
                  سلام{user?.full_name ? `، ${user.full_name}` : ''}! 👋
                </h1>
                <p className="mt-3 text-body leading-7 text-muted">
                  ALEMS یک سیستم‌عامل برای کنکور است: مطالعه‌ات را ثبت می‌کند، سنجش درست می‌دهد و
                  برنامه‌ریزی واقع‌بینانه می‌کند — همه‌چیز با تقویم شمسی و هفته‌ی شنبه تا جمعه.
                  فقط {faDigits(2)} قدم دیگر تا شروع.
                </p>
              </div>
            )}

            {step === 1 && (
              <div className="flex flex-col gap-5">
                <h1 className="text-title-lg font-bold">پروفایل کنکوری</h1>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-body-sm font-semibold">پایه تحصیلی</label>
                    <select
                      value={grade}
                      onChange={(e) => setGrade(e.target.value)}
                      className="w-full rounded-md border border-border bg-surface px-3 py-2.5 text-body outline-none focus:border-primary focus:ring-2 focus:ring-primary/25"
                    >
                      {GRADES.map((g) => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-body-sm font-semibold">رشته</label>
                    <select
                      value={track}
                      onChange={(e) => setTrack(e.target.value)}
                      className="w-full rounded-md border border-border bg-surface px-3 py-2.5 text-body outline-none focus:border-primary focus:ring-2 focus:ring-primary/25"
                    >
                      {TRACKS.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="mb-1.5 block text-body-sm font-semibold">هدف کنکور (اختیاری)</label>
                  <input
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    placeholder="مثلاً: رشته‌ی کامپیوتر دانشگاه صنعتی شریف"
                    className="w-full rounded-md border border-border bg-surface px-3 py-2.5 text-body outline-none focus:border-primary focus:ring-2 focus:ring-primary/25"
                  />
                </div>
                {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{error}</p>}
              </div>
            )}

            {step === 2 && <CheckinCard state={state} onSaved={setState} />}

            {step === 3 && (
              <div className="flex flex-col items-center text-center">
                <motion.div
                  initial={{ scale: 0.4, opacity: 0 }}
                  animate={{ scale: [0.4, 1.1, 1], opacity: 1 }}
                  transition={{ duration: D.slow, ease: EASE_OUT }}
                  className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success-soft text-success"
                >
                  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M4 12.5 9.5 18 20 6.5" />
                  </svg>
                </motion.div>
                <h1 className="text-title-lg font-bold">آماده‌ی شروع!</h1>
                <p className="mt-3 text-body leading-7 text-muted">
                  پروفایل و check-in اولت ذخیره شد. هر روز از بخش «امروز» شروع کن ({formatJalaliLong(todayJalali())}):
                  check-in بزن، برنامه‌ی روز را ببین و مطالعه‌ات را ثبت کن.
                </p>
              </div>
            )}

            {/* nav */}
            <div className="mt-8 flex items-center justify-between">
              <button
                onClick={() => setStep((v) => Math.max(0, v - 1))}
                disabled={step === 0}
                className="rounded-md border border-border px-4 py-2 text-body-sm font-semibold text-ink transition-colors hover:bg-surface-2 disabled:opacity-40"
              >
                قبلی
              </button>
              {step === 1 && (
                <button
                  onClick={saveProfile}
                  disabled={profileSaving}
                  className="flex items-center gap-2 rounded-md bg-primary px-5 py-2 text-body-sm font-semibold text-white shadow-soft transition-opacity hover:opacity-90 disabled:opacity-60"
                >
                  {profileSaving && <Spinner size={14} />}
                  ذخیره و ادامه
                </button>
              )}
              {step !== 1 && (
                <button
                  onClick={() => (step === 2 ? setStep(3) : step === 3 ? navigate('/') : setStep((v) => v + 1))}
                  className="rounded-md bg-primary px-5 py-2 text-body-sm font-semibold text-white shadow-soft transition-opacity hover:opacity-90"
                >
                  {step === 3 ? 'برو به امروز' : 'ادامه'}
                </button>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
