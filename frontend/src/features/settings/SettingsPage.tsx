/**
 * Settings — حساب کاربری (phase 1) + تنظیمات مرور/نمره‌گذاری (phase 4، doc 06/10).
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../app/auth'
import { api, ApiError } from '../../lib/api'
import type { AppSettings } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'

const toFa = (s: string | number) => faDigits(s)

/** کارت تنظیمات مرور + ضریب جریمه کنکور (doc 10 §10.2-10.3، doc 08 §8.1) */
function ReviewSettingsCard() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['settings'], queryFn: () => api.get<AppSettings>('/settings') })
  const [intervals, setIntervals] = useState('')
  const [maxDaily, setMaxDaily] = useState('')
  const [minCluster, setMinCluster] = useState('')
  const [penaltyK, setPenaltyK] = useState('')
  const [includeBlank, setIncludeBlank] = useState(false)
  const [streakGrace, setStreakGrace] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!q.data) return
    setIntervals(q.data.review_intervals.join(', '))
    setMaxDaily(String(q.data.max_daily_review))
    setMinCluster(String(q.data.min_cluster))
    setPenaltyK(String(q.data.konkurs_penalty_k))
    setIncludeBlank(q.data.include_blank_in_review)
    setStreakGrace(String(q.data.streak_grace_days ?? 0))
  }, [q.data])

  const save = useMutation({
    mutationFn: () =>
      api.put<AppSettings>('/settings', {
        review_intervals: intervals
          .split(/[,،\s]+/)
          .filter((x) => x.trim() !== '')
          .map(Number),
        max_daily_review: Number(maxDaily),
        min_cluster: Number(minCluster),
        konkurs_penalty_k: Number(penaltyK),
        include_blank_in_review: includeBlank,
        streak_grace_days: Number(streakGrace === '' ? 0 : streakGrace),
      }),
    onSuccess: (data) => {
      qc.setQueryData(['settings'], data)
      qc.invalidateQueries({ queryKey: ['reviews'] }) // چرخه جدید فوراً در صف اثر کند
      setSaved(true)
      setTimeout(() => setSaved(false), 2200)
    },
  })
  const errMsg = save.error instanceof ApiError ? save.error.message : null

  const num = (v: string) => v.replace(/[۰-۹]/g, (d) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))

  const inputCls =
    'w-full rounded-md border border-border bg-surface px-3 py-2 text-body-sm outline-none focus:border-primary'

  if (q.isPending) {
    return (
      <Card className="mt-4 flex justify-center p-6">
        <Spinner size={18} />
      </Card>
    )
  }

  return (
    <Card className="mt-4 p-4 md:p-5">
      <h2 className="mb-1 text-title-sm font-bold">مرور، نمره‌گذاری و پیوستگی</h2>
      <p className="mb-4 text-body-sm text-muted">
        چرخه مرور فاصله‌ای (روز) — پیش‌فرض {toFa('1, 3, 7, 14')}. تغییرات فوراً در صف مرور و درصد کنکور اثر
        می‌کنند.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-body-sm font-semibold">چرخه مرور (روز، با کاما)</span>
          <input dir="ltr" className={inputCls} value={intervals} onChange={(e) => setIntervals(num(e.target.value))} placeholder="1, 3, 7, 14" aria-label="چرخه مرور" />
        </label>
        <label className="block">
          <span className="mb-1 block text-body-sm font-semibold">ضریب جریمه کنکور (k)</span>
          <input dir="ltr" className={inputCls} value={penaltyK} onChange={(e) => setPenaltyK(num(e.target.value))} placeholder="0.33" aria-label="ضریب جریمه" />
        </label>
        <label className="block">
          <span className="mb-1 block text-body-sm font-semibold">سقف مرور روزانه</span>
          <input dir="ltr" className={inputCls} value={maxDaily} onChange={(e) => setMaxDaily(num(e.target.value))} placeholder="25" aria-label="سقف مرور روزانه" />
        </label>
        <label className="block">
          <span className="mb-1 block text-body-sm font-semibold">حداقل اندازه خوشه</span>
          <input dir="ltr" className={inputCls} value={minCluster} onChange={(e) => setMinCluster(num(e.target.value))} placeholder="8" aria-label="حداقل اندازه خوشه" />
        </label>
        <label className="block">
          <span className="mb-1 block text-body-sm font-semibold">روزهای ارفاق پیوستگی (grace)</span>
          <input dir="ltr" className={inputCls} value={streakGrace} onChange={(e) => setStreakGrace(num(e.target.value))} placeholder="0" aria-label="روزهای ارفاق پیوستگی" />
        </label>
      </div>

      <label className="mt-4 flex cursor-pointer items-center gap-2 text-body-sm">
        <input type="checkbox" checked={includeBlank} onChange={(e) => setIncludeBlank(e.target.checked)} className="accent-[var(--color-primary)]" />
        سوال‌های «نزده» هم وارد صف مرور شوند (پیش‌فرض: فقط غلط‌ها و تیک‌ها)
      </label>

      {errMsg && (
        <p className="mt-3 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">
          {errMsg}
        </p>
      )}

      <div className="mt-4 flex items-center gap-3">
        <Button onClick={() => save.mutate()} disabled={save.isPending} ariaLabel="ذخیره تنظیمات">
          {save.isPending ? <Spinner size={14} /> : null}
          ذخیره
        </Button>
        {saved && <span className="text-body-sm font-semibold text-success">ذخیره شد ✓</span>}
      </div>
    </Card>
  )
}

export function SettingsPage() {
  const { user, student, logout } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  const doLogout = async () => {
    setBusy(true)
    try {
      await logout()
      navigate('/auth', { replace: true })
    } finally {
      setBusy(false)
    }
  }

  const initials = (user?.full_name || user?.email || '?')
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')

  return (
    <Page title="تنظیمات" subtitle="حساب کاربری و تنظیمات ALEMS">
      <Card className="p-4 md:p-5">
        <h2 className="mb-4 text-title-sm font-bold">حساب کاربری</h2>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-primary-soft text-title font-bold text-primary">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-body font-semibold">{user?.full_name || 'کاربر'}</p>
            <p className="truncate text-body-sm text-muted" dir="ltr" style={{ textAlign: 'right' }}>
              {user?.email}
            </p>
            <p className="mt-1 text-body-sm text-muted">
              {student ? (
                <>
                  پایه: <strong className="text-ink">{student.grade ?? '—'}</strong> · رشته:{' '}
                  <strong className="text-ink">{student.track ?? '—'}</strong>
                  {student.target && (
                    <>
                      {' '}
                      · هدف: <strong className="text-ink">{student.target}</strong>
                    </>
                  )}
                </>
              ) : (
                <button onClick={() => navigate('/onboarding')} className="font-semibold text-primary">
                  پروفایل کنکوری را کامل کن
                </button>
              )}
            </p>
          </div>
          <Button variant="danger" onClick={doLogout} disabled={busy} ariaLabel="خروج از حساب">
            {busy ? <Spinner size={14} /> : null}
            خروج
          </Button>
        </div>
      </Card>

      <ReviewSettingsCard />

      <p className="mt-4 px-1 text-body-sm text-muted">
        زمان‌بندی (Asia/Tehran) و زبان (فارسی) همیشه فعال‌اند. گزینه‌های باز: حالت تیره، یادآوری check-in.
      </p>
    </Page>
  )
}
