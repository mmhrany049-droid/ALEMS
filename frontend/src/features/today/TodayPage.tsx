/**
 * Today Hub — «نقش امروز» با داده‌ی واقعی (doc 07.6، doc 11.1، V2-P01).
 * ترتیب اجباری بخش‌ها (doc 07.6، فاز ۸ رعایت شد):
 *   ۱ سلام + check-in سریع انرژی   ۲ خلاصه ظرفیت امروز   ۳ کارهای امروز (checkbox انیمیشنی)
 *   ۴ صف مرور ضروری                ۵ آزمون نزدیک          ۶ پیشنهاد روز با «چرا؟»
 *   ۷ خلاصه ۷ روز (sparkline)      — پیوستگی و پاداش (doc 13) در انتها
 * Motion: cascade بلوک‌ها با todayCascade/todayBlock (doc 07.4 #5) + FocusMode برای کار جاری (doc 07.7).
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { PlanTaskOut, RecommendationOut, RewardsSummary, TodayOut } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { CheckinCard } from '../../components/CheckinCard'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { Icon } from '../../components/Icon'
import { FocusMode } from '../../components/FocusMode'
import { useToast } from '../../app/toast'
import { faDigits } from '../../lib/dates'
import { D, progressFill, successPulse, todayBlock, todayCascade } from '../../motion/variants'

const KIND_BADGE: Record<string, string> = {
  study: 'bg-primary-soft text-primary',
  test: 'bg-warning-soft text-warning',
  review: 'bg-review-soft text-review',
  goal: 'bg-success-soft text-success',
}

export function TodayPage() {
  const qc = useQueryClient()
  const toast = useToast()
  const todayQ = useQuery({ queryKey: ['today'], queryFn: () => api.get<TodayOut>('/today') })
  const d = todayQ.data
  // فاز ۸: حالت تمرکز برای «کار جاری» (doc 07.7)
  const [focusTask, setFocusTask] = useState<PlanTaskOut | null>(null)

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['today'] })
    qc.invalidateQueries({ queryKey: ['state'] })
    qc.invalidateQueries({ queryKey: ['rewards-summary'] }) // هر فعالیت → امتیاز/streak تازه
  }

  const statusM = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'done' | 'pending' }) =>
      api.post<PlanTaskOut>(`/plans/tasks/${id}/status`, { status }),
    onSuccess: invalidate,
  })
  const respondM = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'accepted' | 'rejected' }) =>
      api.post<RecommendationOut>(`/recommendations/${id}/respond`, { status }),
    onSuccess: invalidate,
  })
  const genM = useMutation({
    mutationFn: () => api.post('/plans/generate-week', {}),
    onSuccess: () => {
      invalidate()
      toast.success('برنامهٔ هفته ساخته شد — کارهای امروز را پایین همین پیام ببین.')
    },
  })

  if (todayQ.isPending) {
    return (
      <Page title="امروز">
        <div className="flex flex-col items-center gap-3 py-20 text-muted">
          <Spinner />
          <span className="text-body-sm">در حال چیدن نقش امروز…</span>
        </div>
      </Page>
    )
  }
  if (todayQ.isError || !d) {
    const msg = todayQ.error instanceof ApiError ? todayQ.error.message : 'خطای نامشخص.'
    return (
      <Page title="امروز">
        <EmptyState icon="home" text={msg} action={<Button variant="soft" onClick={() => todayQ.refetch()}>تلاش دوباره</Button>} />
      </Page>
    )
  }

  const cap = d.capacity
  const counts = d.plan_counts
  const pct = counts.total > 0 ? Math.round((counts.done / counts.total) * 100) : 0
  const sparkMax = Math.max(60, ...d.week_sparkline.map((s) => s.done_minutes))

  const toggleTask = (t: PlanTaskOut) =>
    statusM.mutate({ id: t.id, status: t.status === 'done' ? 'pending' : 'done' })

  return (
    <Page title={d.greeting} subtitle={`${d.weekday_fa} ${d.date_jalali} — ظرفیت امروزت ${faDigits(cap.available_minutes)} دقیقه است`}>
      {/* حالت تمرکز — کار جاری (doc 07.7): ناوبری مخفی، تایمر + مشخصات کار، خروج تأییدشده */}
      <AnimatePresence>
        {focusTask && (
          <FocusMode
            title={focusTask.title}
            subtitle={`${focusTask.kind_fa} · ${faDigits(focusTask.minutes)} دقیقه${focusTask.topic_title ? ` · ${focusTask.topic_title}` : ''}`}
            minutes={focusTask.minutes}
            onExit={() => setFocusTask(null)}
          >
            <Card className="flex flex-col gap-3 p-5">
              <p className="text-body leading-7">
                منبع: {focusTask.source_fa}
                {focusTask.reason_fa ? ` · دلیل: ${focusTask.reason_fa}` : ''}
                {focusTask.book_title ? ` · کتاب: ${focusTask.book_title}` : ''}
              </p>
              <p className="rounded-lg bg-surface-2 px-3 py-2 text-body-sm leading-6 text-muted">
                فقط روی همین کار تمرکز کن — وقتی تمام شد، «انجام شد» را بزن.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => {
                    if (focusTask.status !== 'done') toggleTask(focusTask)
                    setFocusTask(null)
                    toast.success('آفرین — کار انجام‌شده ثبت شد.')
                  }}
                  disabled={statusM.isPending}
                >
                  <Icon name="check" size={16} />
                  انجام شد
                </Button>
                <Button variant="ghost" onClick={() => setFocusTask(null)}>
                  بعداً ادامه می‌دهم
                </Button>
              </div>
            </Card>
          </FocusMode>
        )}
      </AnimatePresence>

      <motion.div variants={todayCascade} initial="initial" animate="animate" className="flex flex-col gap-4">
        {/* خطای mutationها */}
        {(statusM.isError || respondM.isError || genM.isError) && (
          <motion.div variants={todayBlock} className="rounded-md bg-danger-soft px-4 py-2.5 text-body-sm text-danger">
            {((statusM.error ?? respondM.error ?? genM.error) as ApiError)?.message}
          </motion.div>
        )}

        {/* ۱) سلام + check-in سریع انرژی و ۲) خلاصه ظرفیت امروز (doc 07.6 #1-2) */}
        <div className="grid gap-4 lg:grid-cols-2">
          <motion.div variants={todayBlock}>
            <CheckinCard state={d.checkin} onSaved={invalidate} />
          </motion.div>
          <motion.div variants={todayBlock}>
            <Card className="h-full p-4 md:p-5">
              <div className="mb-3 flex items-center gap-2">
                <Icon name="clock" size={18} />
                <h2 className="text-title-sm font-bold">ظرفیت امروز</h2>
                {cap.source === 'override' && (
                  <span className="mr-auto rounded-md bg-warning-soft px-2 py-0.5 text-[11px] font-semibold text-warning">override</span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                <Stat label="زمان آزاد مطالعه" value={`${faDigits(cap.available_minutes)} دقیقه`} />
                <Stat label="وعده پیشنهادی" value={`${faDigits(cap.suggested_session_count)} وعده ۶۰–۱۲۰ دقیقه`} />
                <Stat label="مدرسه/کلاس" value={`${faDigits(cap.school_minutes + cap.class_minutes)} دقیقه`} />
                <Stat label="انجام ۷ روز اخیر" value={`${faDigits(Math.round(cap.completion_rate * 100))}٪`} />
              </div>
              <p className="mt-3 text-body-sm leading-6 text-muted">
                ضریب حالت امروز (انرژی/تمرکز، وزن پایین): <strong className="text-ink">{faDigits(cap.state_factor)}</strong>
                {' '}— وقت آزاد ≠ ظرفیت؛ ظرفیت یعنی زمانی که واقعاً می‌توانی مطالعه کنی.
              </p>
            </Card>
          </motion.div>
        </div>

        {/* ۳) کارهای امروز — checkbox انیمیشنی + دکمه تمرکز (doc 07.6 #3، doc 07.7) */}
        <motion.div variants={todayBlock}>
          <Card className="p-4 md:p-5">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Icon name="plan" size={18} />
              <h2 className="text-title-sm font-bold">کارهای امروز</h2>
              <span className="text-body-sm text-muted">
                {faDigits(counts.done)} از {faDigits(counts.total)} کار انجام شد
              </span>
              {counts.total > 0 && (
                <span className="mr-auto text-body-sm font-semibold text-primary">{faDigits(pct)}٪</span>
              )}
            </div>
            {counts.total > 0 && (
              <div className="mb-4 h-2 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
                <motion.div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${pct}%` }}
                  variants={progressFill}
                  initial="initial"
                  animate="animate"
                />
              </div>
            )}
            {d.plan_items.length === 0 ? (
              <EmptyState
                icon="plan"
                text="برای امروز کاری نداری — هفته را بساز تا planner با ظرفیت واقعی برایت بچیند."
                action={
                  <Button onClick={() => genM.mutate()} disabled={genM.isPending}>
                    {genM.isPending ? 'در حال ساخت…' : 'ساخت برنامه هفته'}
                  </Button>
                }
              />
            ) : (
              <ul className="flex flex-col gap-1.5">
                {d.plan_items.map((t) => (
                  <TaskRow
                    key={t.id}
                    task={t}
                    busy={statusM.isPending}
                    onToggle={() => toggleTask(t)}
                    onFocus={() => setFocusTask(t)}
                  />
                ))}
              </ul>
            )}
          </Card>
        </motion.div>

        {/* ۴) صف مرور ضروری و ۵) آزمون نزدیک (doc 07.6 #4-5) */}
        <div className="grid gap-4 lg:grid-cols-2">
          <motion.div variants={todayBlock}>
            <Card className="h-full p-4 md:p-5">
              <div className="mb-3 flex items-center gap-2">
                <Icon name="review" size={18} />
                <h2 className="text-title-sm font-bold">صف مرور ضروری</h2>
                <span className="mr-auto rounded-md bg-review-soft px-2 py-0.5 text-[11px] font-semibold text-review">
                  {faDigits(d.review_due_count)} آیتم
                </span>
              </div>
              {d.review_top.length === 0 ? (
                <p className="text-body-sm text-muted">صف مرور خالی است — آفرین، چیزی سررسید نشده.</p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {d.review_top.map((r) => (
                    <li key={r.id} className="flex items-center gap-2 rounded-md px-2 py-2 hover:bg-surface-2">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-review-soft text-[11px] font-bold text-review">
                        {faDigits(r.number ?? '؟')}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-body-sm font-medium">{r.topic_title ?? 'موضوع نامشخص'}</p>
                        <p className="truncate text-[11px] text-muted">{r.book_title ?? ''} · {r.source_fa}</p>
                      </div>
                      {r.critical && (
                        <span className="shrink-0 rounded-md bg-danger-soft px-1.5 py-0.5 text-[10px] font-semibold text-danger">بحرانی</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3">
                <Button variant="soft" to="/review">برو به صف مرور</Button>
              </div>
            </Card>
          </motion.div>

          {/* ۵) آزمون نزدیک — بلوک مستقل (doc 07.6 #5، فاز ۶/۸) */}
          <motion.div variants={todayBlock}>
            <Card className="h-full p-4 md:p-5">
              <div className="mb-3 flex items-center gap-2">
                <Icon name="exam" size={18} />
                <h2 className="text-title-sm font-bold">آزمون نزدیک</h2>
                <Link to="/exams" className="mr-auto text-body-sm font-semibold text-primary hover:underline">همهٔ آزمون‌ها ←</Link>
              </div>
              {d.upcoming_exams.length === 0 ? (
                <EmptyState icon="exam" text="در ۷ روز آینده آزمونی نداری — هدف‌گذاری کن تا برنامه بر اساس آن بچرخد." action={<Button variant="soft" to="/exams">ثبت آزمون</Button>} />
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {d.upcoming_exams.map((e) => (
                    <li key={e.id} className="flex items-center justify-between gap-2 rounded-lg bg-surface-2 px-3 py-2">
                      <div className="min-w-0">
                        <p className="truncate text-body-sm font-semibold">{e.title}</p>
                        <p className="text-[10px] text-muted">
                          {e.kind_fa}
                          {e.scheduled_date_jalali ? ` · ${faDigits(e.scheduled_date_jalali)}` : ''}
                          {e.subjects.length > 0 ? ` · ${e.subjects.join('، ')}` : ''}
                        </p>
                      </div>
                      <span
                        className={[
                          'shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold',
                          e.days_until <= 1 ? 'bg-danger-soft text-danger' : 'bg-primary-soft text-primary',
                        ].join(' ')}
                      >
                        {e.days_until === 0 ? 'امروز!' : e.days_until === 1 ? 'فردا' : `${faDigits(e.days_until)} روز دیگر`}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </motion.div>
        </div>

        {/* ۶) پیشنهاد روز با «چرا؟» (doc 07.6 #6، doc 11.6، doc 08 §8.10) */}
        {d.recommendation && (
          <motion.div variants={todayBlock}>
            <RecommendationCard
              rec={d.recommendation}
              busy={respondM.isPending}
              onRespond={(status) => respondM.mutate({ id: d.recommendation!.id, status })}
            />
          </motion.div>
        )}

        {/* ۷) خلاصه ۷ روز — نوار هفته + sparkline (doc 07.6 #7) */}
        <motion.div variants={todayBlock}>
          <Card className="p-4 md:p-5">
            <div className="mb-3 flex items-center gap-2">
              <Icon name="progress" size={18} />
              <h2 className="text-title-sm font-bold">هفته {d.week.week_start_jalali}</h2>
              <Link to="/plan" className="mr-auto text-body-sm font-semibold text-primary hover:underline">برنامه هفته ←</Link>
            </div>
            <div className="grid grid-cols-7 gap-1.5">
              {d.week.days.map((w) => (
                <div
                  key={w.date}
                  className={[
                    'flex flex-col items-center gap-1 rounded-md border px-1 py-2',
                    w.is_today ? 'border-primary bg-primary-soft' : 'border-border bg-surface-2/60',
                  ].join(' ')}
                >
                  <span className="text-[10px] text-muted">{w.weekday_fa.slice(0, 3)}</span>
                  <span className="text-body-sm font-bold">{faDigits(w.date_jalali.slice(-2))}</span>
                  <span className="text-[10px] text-muted">
                    {faDigits(w.done_count)}/{faDigits(w.tasks_count)}
                  </span>
                </div>
              ))}
            </div>
            {/* sparkline هفت روز اخیر — دقیقه انجام‌شده + تعداد تست */}
            <div className="mt-4">
              <p className="mb-2 text-body-sm text-muted">۷ روز اخیر — دقیقه مطالعه و تعداد تست</p>
              <div className="flex items-end gap-1.5" style={{ height: 72 }}>
                {d.week_sparkline.map((s) => (
                  <div key={s.date} className="flex flex-1 flex-col items-center gap-1">
                    <motion.div
                      className={['w-full rounded-t-md', s.is_today ? 'bg-primary' : 'bg-primary/45'].join(' ')}
                      initial={{ height: 0 }}
                      animate={{ height: Math.max(3, (s.done_minutes / sparkMax) * 48) }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                      title={`${s.done_minutes} دقیقه`}
                    />
                    <span className="text-[9px] text-muted">{faDigits(s.attempts)}ت</span>
                    <span className={['text-[9px]', s.is_today ? 'font-bold text-primary' : 'text-muted'].join(' ')}>
                      {s.weekday_fa.slice(0, 3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>

        {/* پیوستگی و پاداش (doc 13 — فاز ۷)؛ بیرون از فهرست ۷گانهٔ doc 07.6 → انتها */}
        <motion.div variants={todayBlock}>
          <RewardsCard />
        </motion.div>
      </motion.div>
    </Page>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-surface-2 px-3 py-2.5">
      <p className="text-[11px] text-muted">{label}</p>
      <p className="mt-0.5 text-body-sm font-bold">{value}</p>
    </div>
  )
}

function RecommendationCard({ rec, busy, onRespond }: { rec: RecommendationOut; busy: boolean; onRespond: (s: 'accepted' | 'rejected') => void }) {
  const answered = rec.status !== 'suggested'
  const [why, setWhy] = useState(false)
  return (
    <Card className="border-primary/40 bg-primary-soft/40 p-4 md:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Icon name="sparkle" size={18} />
        <h2 className="text-title-sm font-bold">پیشنهاد امروز</h2>
        {answered && (
          <span className={[
            'rounded-md px-2 py-0.5 text-[11px] font-semibold',
            rec.status === 'accepted' ? 'bg-success-soft text-success' : 'bg-surface-2 text-muted',
          ].join(' ')}>
            {rec.status === 'accepted' ? 'پذیرفتی ✓' : 'رد شد'}
          </span>
        )}
      </div>
      <p className="mt-2 text-body font-semibold">{rec.payload.title}</p>
      {typeof rec.payload.minutes === 'number' && rec.payload.minutes > 0 && (
        <p className="text-body-sm text-muted">{faDigits(rec.payload.minutes)} دقیقه</p>
      )}
      {/* دلیل(ها) — doc 08 §8.10: هر پیشنهاد ≥۱ دلیل با کد قابل ترجمه */}
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {rec.reasons.map((r) => (
          <span key={r.code} className="rounded-md bg-surface px-2 py-0.5 text-[11px] font-medium text-muted" title={r.code}>
            {r.fa}
          </span>
        ))}
        <button
          type="button"
          onClick={() => setWhy((v) => !v)}
          className="mr-auto rounded-md px-2 py-0.5 text-[11px] font-bold text-primary hover:underline"
          aria-expanded={why}
        >
          {why ? 'بستن «چرا»' : 'چرا این پیشنهاد؟'}
        </button>
      </div>
      {/* چرا این پیشنهاد؟ — توضیح فارسی با عدد و شاهد (doc 07 §7.6 #6، فاز ۷) */}
      <AnimatePresence initial={false}>
        {why && (
          <motion.div
            key="why"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <p className="mt-2 rounded-lg bg-surface px-3 py-2 text-body-sm leading-6">
              {rec.payload.explain_fa ?? rec.reasons.map((r) => r.fa).join(' · ')}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
      {!answered && (
        <div className="mt-3 flex gap-2">
          <Button onClick={() => onRespond('accepted')} disabled={busy}>می‌پذیرم — شروع کن</Button>
          <Button variant="ghost" onClick={() => onRespond('rejected')} disabled={busy}>رد کن</Button>
        </div>
      )}
    </Card>
  )
}

function TaskRow({ task, busy, onToggle, onFocus }: { task: PlanTaskOut; busy: boolean; onToggle: () => void; onFocus: () => void }) {
  const [open, setOpen] = useState(false)
  const done = task.status === 'done'
  return (
    <li className="rounded-md border border-transparent hover:border-border">
      <div className="flex items-center gap-2.5 px-2 py-2">
        {/* checkbox انیمیشنی (doc 07.6 #3) — tap scale + تیک با successPulse */}
        <motion.button
          type="button"
          whileTap={{ scale: 0.82 }}
          transition={{ duration: D.fast }}
          onClick={onToggle}
          disabled={busy}
          aria-label={done ? 'برگردان به انجام‌نشده' : 'انجام شد'}
          className={[
            'relative flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full border-2 transition-colors',
            done ? 'border-success bg-success text-white' : 'border-border hover:border-primary',
          ].join(' ')}
        >
          <AnimatePresence>
            {done && (
              <motion.span key="tick" variants={successPulse} initial="initial" animate="animate" exit={{ opacity: 0 }} className="flex items-center justify-center">
                <Icon name="check" size={13} />
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>
        <div className="min-w-0 flex-1">
          <p className={['truncate text-body-sm font-medium', done ? 'text-muted line-through' : ''].join(' ')}>{task.title}</p>
          <p className="truncate text-[11px] text-muted">
            {faDigits(task.minutes)} دقیقه{task.count ? ` · ${faDigits(task.count)} آیتم` : ''}{task.topic_title ? ` · ${task.topic_title}` : ''}
          </p>
        </div>
        <span className={['shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-semibold', KIND_BADGE[task.kind] ?? 'bg-surface-2 text-muted'].join(' ')}>
          {task.kind_fa}
        </span>
        {task.locked && (
          <span className="shrink-0 rounded-md bg-warning-soft px-1.5 py-0.5 text-[10px] font-semibold text-warning">قفل</span>
        )}
        {/* حالت تمرکز برای کار جاری (doc 07.7) */}
        {!done && (
          <motion.button
            type="button"
            whileTap={{ scale: 0.9 }}
            transition={{ duration: D.fast }}
            onClick={onFocus}
            aria-label={`حالت تمرکز برای ${task.title}`}
            title="حالت تمرکز"
            className="shrink-0 rounded-md p-1 text-muted hover:bg-primary-soft hover:text-primary"
          >
            <Icon name="focus" size={16} />
          </motion.button>
        )}
        <button type="button" onClick={() => setOpen(!open)} className="shrink-0 px-1 text-muted hover:text-ink" aria-label="جزئیات">
          <Icon name="more" size={16} />
        </button>
      </div>
      {open && (
        <div className="border-t border-border px-3 py-2 text-[11px] leading-5 text-muted">
          منبع: {task.source_fa}{task.reason_fa ? ` · دلیل: ${task.reason_fa}` : ''}
          {task.book_title ? ` · کتاب: ${task.book_title}` : ''}
          {task.status === 'skipped' && ' · رد شده'}
        </div>
      )}
    </li>
  )
}

/** پیوستگی + امتیاز + نشان‌ها (doc 13) — streak فقط با فعالیت مطالعاتی معتبر (§8.9) */
function RewardsCard() {
  const q = useQuery({ queryKey: ['rewards-summary'], queryFn: () => api.get<RewardsSummary>('/rewards/summary') })
  if (q.isLoading) return <Card className="flex justify-center p-5"><Spinner /></Card>
  if (q.isError || !q.data) return null
  const s = q.data
  return (
    <Card className="p-4 md:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Icon name="sparkle" size={18} />
        <h2 className="text-title-sm font-bold">پیوستگی و پاداش</h2>
        <span className="mr-auto text-[11px] text-muted">
          {faDigits(s.badges.earned_count)} از {faDigits(s.badges.total)} نشان
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2.5">
        <Stat label="پیوستگی جاری" value={`${'🔥'} ${faDigits(s.streak.current)} روز`} />
        <Stat label="رکورد پیوستگی" value={`${faDigits(s.streak.longest)} روز`} />
        <Stat label="امتیاز کل" value={faDigits(s.points_total)} />
      </div>
      {s.streak.grace_days > 0 && (
        <p className="mt-2 text-[11px] text-muted">{faDigits(s.streak.grace_days)} روز ارفاق فعال است.</p>
      )}
      {s.badges.recent.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {s.badges.recent.map((b) => (
            <span key={b.code} className="rounded-md bg-warning-soft px-2 py-0.5 text-[11px] font-semibold text-warning">
              {b.title_fa} 🏅
            </span>
          ))}
        </div>
      )}
      {/* habit advice — فقط وقتی ۳۰ روز داده هست نمایش داده می‌شود (doc 08 §8.9) */}
      {s.habit_advice.available && s.habit_advice.message_fa && (
        <p className="mt-3 rounded-lg bg-surface-2 px-3 py-2 text-body-sm leading-6">{s.habit_advice.message_fa}</p>
      )}
      {/* procrastination aid (doc 13.5) */}
      {s.procrastination && (
        <p className="mt-2 rounded-lg bg-warning-soft px-3 py-2 text-body-sm leading-6 text-warning">
          {s.procrastination.message_fa}
        </p>
      )}
    </Card>
  )
}
