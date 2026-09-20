/**
 * Settings — حساب کاربری (phase 1) + تنظیمات مرور/نمره‌گذاری (phase 4، doc 06/10).
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from '../../app/auth'
import { useToast } from '../../app/toast'
import { api, apiBlob, saveBlob, ApiError } from '../../lib/api'
import type { AppSettings, BackupList, BackupMeta, RestoreOut } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { ConfirmButton } from '../../components/ConfirmButton'
import { Icon } from '../../components/Icon'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT } from '../../motion/variants'

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

/**
 * پشتیبان‌گیری و بازیابی (doc 04 «دستی، خودکار، AES»، doc 06 §Backup، V2-S01/S02).
 * ساخت با label/رمز اختیاری · لیست · دانلود · بازیابی با تأیید دومرحله‌ای (doc 07.9).
 */
function BackupCard() {
  const qc = useQueryClient()
  const toast = useToast()
  const listQ = useQuery({ queryKey: ['backups'], queryFn: () => api.get<BackupList>('/backup/list') })
  const settingsQ = useQuery({ queryKey: ['settings'], queryFn: () => api.get<AppSettings>('/settings') })

  const [label, setLabel] = useState('')
  const [password, setPassword] = useState('')
  const [restoreId, setRestoreId] = useState<string | null>(null)
  const [restorePw, setRestorePw] = useState('')

  const createM = useMutation({
    mutationFn: () =>
      api.post<BackupMeta>('/backup/create', {
        label: label.trim() || null,
        password: password.trim() ? password.trim() : null,
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['backups'] })
      toast.success(`فایل پشتیبان ساخته شد — ${data.id}${data.encrypted ? ' (رمزدار 🔒)' : ''}`)
      setLabel('')
      setPassword('')
    },
  })
  const autoM = useMutation({
    mutationFn: (v: boolean) => api.put<AppSettings>('/settings', { auto_backup: v }),
    onSuccess: (data) => {
      qc.setQueryData(['settings'], data)
      toast.success(data.auto_backup ? 'پشتیبان خودکار روشن شد — در هر راه‌اندازی سرور.' : 'پشتیبان خودکار خاموش شد.')
    },
  })
  const restoreM = useMutation({
    mutationFn: (id: string) =>
      api.post<RestoreOut>('/backup/restore', { id, confirm: true, password: restorePw.trim() || null }),
    onSuccess: (data) => {
      setRestoreId(null)
      setRestorePw('')
      // کل داده عوض شده — همهٔ کش‌ها باطل شود (doc 15 V2-S01)
      void qc.invalidateQueries()
      toast.success(data.message_fa)
    },
  })
  const download = async (id: string) => {
    try {
      const { blob, filename } = await apiBlob(`/backup/download/${id}`)
      saveBlob(blob, filename)
      toast.success('دانلود فایل پشتیبان شروع شد.')
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : 'دانلود ناموفق بود.')
    }
  }

  const errMsg = (createM.error ?? restoreM.error ?? autoM.error) as ApiError | null
  const items = listQ.data?.items ?? []
  const inputCls = 'w-full rounded-md border border-border bg-surface px-3 py-2 text-body-sm outline-none focus:border-primary'

  return (
    <Card className="mt-4 p-4 md:p-5">
      <div className="mb-1 flex items-center gap-2">
        <Icon name="shield" size={18} />
        <h2 className="text-title-sm font-bold">پشتیبان‌گیری و بازیابی</h2>
      </div>
      <p className="mb-4 text-body-sm text-muted">
        از کل داده‌ها (کتاب‌ها، تست‌ها، برنامه، پاداش) فایل zip ساخته می‌شود؛ رمز AES اختیاری است.
        بازیابی کل دادهٔ جاری را جایگزین می‌کند — با تأیید دومرحله‌ای.
      </p>

      {/* ساخت پشتیبان */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <input className={inputCls} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="برچسب (اختیاری) — مثلاً قبل از کنکور" aria-label="برچسب پشتیبان" />
        <input className={inputCls} dir="ltr" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="رمز AES (اختیاری، ≥۴)" aria-label="رمز پشتیبان" />
        <Button onClick={() => createM.mutate()} disabled={createM.isPending} className="shrink-0">
          {createM.isPending ? <Spinner size={14} /> : null}
          ساخت پشتیبان
        </Button>
      </div>

      {/* خودکار (doc 04) */}
      <label className="mt-3 flex cursor-pointer items-center gap-2 text-body-sm">
        <input
          type="checkbox"
          checked={settingsQ.data?.auto_backup ?? false}
          onChange={(e) => autoM.mutate(e.target.checked)}
          disabled={autoM.isPending || settingsQ.isPending}
          className="accent-[var(--color-primary)]"
        />
        پشتیبان خودکار در راه‌اندازی سرور (بدون رمز)
      </label>

      {errMsg && (
        <p className="mt-3 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{errMsg.message}</p>
      )}

      {/* لیست */}
      <div className="mt-4">
        {listQ.isPending ? (
          <div className="flex justify-center py-3"><Spinner size={16} /></div>
        ) : items.length === 0 ? (
          <p className="rounded-lg bg-surface-2 px-3 py-3 text-body-sm text-muted">
            هنوز پشتیبانی نداری — همین بالا «ساخت پشتیبان» را بزن.
          </p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {items.map((b) => (
              <li key={b.id} className="rounded-lg border border-border bg-surface-2/50 px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-body-sm font-semibold">
                    {faDigits(b.created_at_jalali)} <span className="text-[11px] font-normal text-muted">{b.created_at_local}</span>
                  </span>
                  {b.label && <span className="rounded-md bg-primary-soft px-2 py-0.5 text-[11px] font-semibold text-primary">{b.label}</span>}
                  {b.encrypted && <span className="rounded-md bg-warning-soft px-2 py-0.5 text-[11px] font-semibold text-warning">رمزدار 🔒</span>}
                  <span className="text-[11px] text-muted">
                    {b.size_bytes != null ? `${faDigits(Math.max(1, Math.round(b.size_bytes / 1024)))} کیلوبایت` : ''}
                  </span>
                  <div className="mr-auto flex items-center gap-1.5">
                    <Button variant="ghost" className="!px-2.5 !py-1 !text-[11px]" onClick={() => void download(b.id)} ariaLabel="دانلود">
                      <Icon name="download" size={13} /> دانلود
                    </Button>
                    <ConfirmButton
                      onConfirm={() => restoreM.mutate(b.id)}
                      busy={restoreM.isPending && restoreId === b.id}
                      disabled={restoreM.isPending}
                      label="بازیابی"
                      confirmLabel="کل دادهٔ جاری جایگزین شود؟"
                      className="!px-2.5 !py-1 !text-[11px]"
                    />
                  </div>
                </div>
                {/* رمز برای پشتیبان رمزدار — قبل از تأیید نهایی */}
                <AnimatePresence>
                  {restoreId === b.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto', transition: { duration: D.fast, ease: EASE_OUT } }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-2 flex items-center gap-2">
                        <input
                          className={inputCls}
                          dir="ltr"
                          type="password"
                          value={restorePw}
                          onChange={(e) => setRestorePw(e.target.value)}
                          placeholder="رمز این پشتیبان"
                          aria-label="رمز بازیابی"
                        />
                        <Button variant="ghost" className="shrink-0" onClick={() => { setRestoreId(null); setRestorePw('') }}>بستن</Button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
                {b.encrypted && (
                  <button
                    type="button"
                    onClick={() => { setRestoreId(restoreId === b.id ? null : b.id); setRestorePw('') }}
                    className="mt-1 text-[11px] font-bold text-primary hover:underline"
                  >
                    {restoreId === b.id ? 'بستن ورود رمز' : 'بازیابی با رمز…'}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
        {listQ.data && (
          <p className="mt-2 text-[11px] text-muted">
            {faDigits(listQ.data.count)} پشتیبان · نگهداری خودکار تا {faDigits(listQ.data.retention)} مورد آخر
          </p>
        )}
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

      {/* پشتیبان‌گیری و بازیابی (doc 04، V2-S01/S02) */}
      <BackupCard />

      <p className="mt-4 px-1 text-body-sm text-muted">
        زمان‌بندی (Asia/Tehran) و زبان (فارسی) همیشه فعال‌اند. گزینه‌های باز: حالت تیره، یادآوری check-in.
      </p>
    </Page>
  )
}
