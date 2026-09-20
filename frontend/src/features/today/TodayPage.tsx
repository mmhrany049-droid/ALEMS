/**
 * Today Hub — «نقش امروز» با داده‌ی واقعی (doc 07.6، doc 11.1، V2-P01).
 * بخش‌ها: check-in + ظرفیت · پیشنهاد روز · برنامه امروز · مرور ضروری · هفته · sparkline.
 * Motion: cascade بلوک‌ها با todayCascade/todayBlock (doc 07.4 #5).
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { PlanTaskOut, RecommendationOut, TodayOut } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { CheckinCard } from '../../components/CheckinCard'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { Icon } from '../../components/Icon'
import { faDigits } from '../../lib/dates'
import { progressFill, todayBlock, todayCascade } from '../../motion/variants'

const KIND_BADGE: Record<string, string> = {
  study: 'bg-primary-soft text-primary',
  test: 'bg-warning-soft text-warning',
  review: 'bg-review-soft text-review',
  goal: 'bg-success-soft text-success',
}

export function TodayPage() {
  const qc = useQueryClient()
  const todayQ = useQuery({ queryKey: ['today'], queryFn: () => api.get<TodayOut>('/today') })
  const d = todayQ.data

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['today'] })
    qc.invalidateQueries({ queryKey: ['state'] })
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
    onSuccess: invalidate,
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

  return (
    <Page title={d.greeting} subtitle={`${d.weekday_fa} ${d.date_jalali} — ظرفیت امروزت ${faDigits(cap.available_minutes)} دقیقه است`}>
      <motion.div variants={todayCascade} initial="initial" animate="animate" className="flex flex-col gap-4">
        {/* خطای mutationها */}
        {(statusM.isError || respondM.isError || genM.isError) && (
          <motion.div variants={todayBlock} className="rounded-md bg-danger-soft px-4 py-2.5 text-body-sm text-danger">
            {((statusM.error ?? respondM.error ?? genM.error) as ApiError)?.message}
          </motion.div>
        )}

        {/* ۱) check-in + ۲) ظرفیت (doc 07.6 بخش حالت و ظرفیت) */}
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

        {/* ۳) پیشنهاد روز (doc 11.6 — یک کار مشخص، accept/reject) */}
        {d.recommendation && (
          <motion.div variants={todayBlock}>
            <RecommendationCard
              rec={d.recommendation}
              busy={respondM.isPending}
              onRespond={(status) => respondM.mutate({ id: d.recommendation!.id, status })}
            />
          </motion.div>
        )}

        {/* ۴) برنامه امروز (doc 07.6 — چک‌لیست واقعی) */}
        <motion.div variants={todayBlock}>
          <Card className="p-4 md:p-5">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Icon name="plan" size={18} />
              <h2 className="text-title-sm font-bold">برنامه امروز</h2>
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
                    onToggle={() => statusM.mutate({ id: t.id, status: t.status === 'done' ? 'pending' : 'done' })}
                  />
                ))}
              </ul>
            )}
          </Card>
        </motion.div>

        {/* ۵) مرور ضروری + ۶) نوار هفته */}
        <div className="grid gap-4 lg:grid-cols-2">
          <motion.div variants={todayBlock}>
            <Card className="h-full p-4 md:p-5">
              <div className="mb-3 flex items-center gap-2">
                <Icon name="review" size={18} />
                <h2 className="text-title-sm font-bold">مرورهای سررسیده</h2>
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

          <motion.div variants={todayBlock}>
            <Card className="h-full p-4 md:p-5">
              <div className="mb-3 flex items-center gap-2">
                <Icon name="target" size={18} />
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
              {/* ۵) آزمون نزدیک — فاز ۶ (doc 07 §7.6) */}
              <div className="mt-3 border-t border-border pt-3">
                <p className="text-[11px] font-semibold text-muted">آزمون نزدیک (۷ روز آینده)</p>
                {d.upcoming_exams.length === 0 ? (
                  <p className="mt-1 text-[11px] text-muted">فعلاً آزمونی ثبت نشده است.</p>
                ) : (
                  <div className="mt-1.5 space-y-1.5">
                    {d.upcoming_exams.map((e) => (
                      <div key={e.id} className="flex items-center justify-between gap-2 rounded-lg bg-surface-2 px-3 py-2">
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
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        </div>
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
      <div className="mt-2 flex flex-wrap gap-1.5">
        {rec.reasons.map((r) => (
          <span key={r.code} className="rounded-md bg-surface px-2 py-0.5 text-[11px] font-medium text-muted" title={r.code}>
            {r.fa}
          </span>
        ))}
      </div>
      {!answered && (
        <div className="mt-3 flex gap-2">
          <Button onClick={() => onRespond('accepted')} disabled={busy}>می‌پذیرم — شروع کن</Button>
          <Button variant="ghost" onClick={() => onRespond('rejected')} disabled={busy}>رد کن</Button>
        </div>
      )}
    </Card>
  )
}

function TaskRow({ task, busy, onToggle }: { task: PlanTaskOut; busy: boolean; onToggle: () => void }) {
  const [open, setOpen] = useState(false)
  const done = task.status === 'done'
  return (
    <li className="rounded-md border border-transparent hover:border-border">
      <div className="flex items-center gap-2.5 px-2 py-2">
        <button
          type="button"
          onClick={onToggle}
          disabled={busy}
          aria-label={done ? 'برگردان به انجام‌نشده' : 'انجام شد'}
          className={[
            'flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full border-2 transition-colors',
            done ? 'border-success bg-success text-white' : 'border-border hover:border-primary',
          ].join(' ')}
        >
          {done && <Icon name="check" size={13} />}
        </button>
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
