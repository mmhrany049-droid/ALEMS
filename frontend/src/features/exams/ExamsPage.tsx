/**
 * Exams — Exam Center (doc 12، فاز ۶).
 * - چرخه: planned → in_progress → finished (+ cancelled)
 * - ثبت نتیجه: از جلسه‌های تست (merge) یا شمارش دستی
 * - scoring کنکوری/بدون‌جریمه همیشه دو عدد جدا (doc 08 §8.1 — V2-A01 spirit)
 * - کارنامه: درصد‌ها + شمارش‌ها + جلسات + topics (doc 12.2)
 * - V2 UI + Framer Motion (قید ۵)
 */
import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type {
  BookResource,
  ExamCreateIn,
  ExamKind,
  ExamListOut,
  ExamOut,
  ExamResultOut,
  ExamSubmitIn,
  TestSessionOut,
} from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, fadeInUp, listItem, modal, staggerList } from '../../motion/variants'

const KINDS: { id: ExamKind; fa: string }[] = [
  { id: 'mock', fa: 'آزمایشی' },
  { id: 'school_subject', fa: 'امتحان درسی' },
  { id: 'free', fa: 'آزاد' },
]

const STATUS_TONE: Record<string, string> = {
  planned: 'bg-primary-soft text-primary',
  in_progress: 'bg-warning-soft text-warning',
  finished: 'bg-success-soft text-success',
  cancelled: 'bg-surface-2 text-muted',
}

/** ارقام فارسی → عدد (الگوی SettingsPage) */
const num = (v: string): number => Number(v.replace(/[\u06F0-\u06F9]/g, (d) => String('\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9'.indexOf(d))).replace(/[^\d.-]/g, ''))

const pct = (v: number | null) => (v === null || v === undefined ? '—' : `${faDigits(Math.round(v * 10) / 10)}٪`)

export function ExamsPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [submitFor, setSubmitFor] = useState<ExamOut | null>(null)
  const [resultFor, setResultFor] = useState<string | null>(null)

  const examsQ = useQuery({
    queryKey: ['exams'],
    queryFn: () => api.get<ExamListOut>('/exams'),
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['exams'] })
    qc.invalidateQueries({ queryKey: ['today'] })
    qc.invalidateQueries({ queryKey: ['overview'] })
  }

  const cancelM = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'cancelled' | 'planned' }) =>
      api.put<ExamOut>(`/exams/${id}`, { status }),
    onSuccess: invalidate,
  })
  const startM = useMutation({
    mutationFn: (id: string) => api.post<ExamOut>(`/exams/${id}/start`),
    onSuccess: invalidate,
  })
  const deleteM = useMutation({
    mutationFn: (id: string) => api.del<{ deleted: boolean }>(`/exams/${id}`),
    onSuccess: invalidate,
  })

  const items = examsQ.data?.items ?? []
  const active = items.filter((e) => e.status === 'planned' || e.status === 'in_progress')
  const finished = items.filter((e) => e.status === 'finished')
  const cancelled = items.filter((e) => e.status === 'cancelled')
  const avgPk = useMemo(() => {
    const vals = finished.map((e) => e.scoring?.percent_konkur).filter((v): v is number => v !== null && v !== undefined)
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
  }, [finished])

  if (examsQ.isLoading) {
    return (
      <Page title="آزمون‌ها" subtitle="Exam Center — آزمایشی، امتحان درسی، آزاد">
        <div className="flex justify-center py-16"><Spinner /></div>
      </Page>
    )
  }
  if (examsQ.isError) {
    const msg = examsQ.error instanceof ApiError ? examsQ.error.message : 'خطا در دریافت آزمون‌ها.'
    return (
      <Page title="آزمون‌ها">
        <EmptyState icon="exam" text={msg} action={<Button variant="soft" onClick={() => examsQ.refetch()}>تلاش دوباره</Button>} />
      </Page>
    )
  }

  return (
    <Page title="آزمون‌ها" subtitle="آزمایشی و امتحان با درصد کنکوری و بدون جریمه — همیشه جدا">
      <motion.div variants={staggerList} initial="initial" animate="animate" className="space-y-5">
        {/* --- آمار بالا --- */}
        <motion.div variants={listItem} className="grid grid-cols-3 gap-3">
          <MiniStat label="پیش‌رو" value={faDigits(examsQ.data?.upcoming_count ?? 0)} tone="text-primary" />
          <MiniStat label="تمام‌شده" value={faDigits(finished.length)} tone="text-success" />
          <MiniStat label="میانگین درصد کنکوری" value={pct(avgPk)} tone="text-ink" />
        </motion.div>

        {/* --- ثبت آزمون --- */}
        <motion.div variants={listItem}>
          <div className="flex items-center justify-between">
            <h2 className="text-title-sm font-bold">آزمون‌های پیش‌رو</h2>
            <Button variant={showCreate ? 'soft' : 'primary'} onClick={() => setShowCreate((v) => !v)}>
              {showCreate ? 'بستن فرم' : '+ ثبت آزمون'}
            </Button>
          </div>
          <AnimatePresence>
            {showCreate && (
              <motion.div key="create" variants={modal} initial="initial" animate="animate" exit="exit" className="mt-3">
                <CreateExamForm
                  onDone={() => { setShowCreate(false); invalidate() }}
                  onCancel={() => setShowCreate(false)}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* --- لیست فعال --- */}
        <motion.div variants={listItem} className="space-y-3">
          {active.length === 0 && !showCreate && (
            <Card className="p-5 text-body-sm text-muted">
              آزمونی پیش رو نیست. یک آزمون ثبت کن تا در «امروز» و اولویت‌بندی هفته هم دیده شود.
            </Card>
          )}
          {active.map((e) => (
            <ExamCard
              key={e.id}
              exam={e}
              busy={startM.isPending || cancelM.isPending || deleteM.isPending}
              onStart={() => startM.mutate(e.id)}
              onSubmit={() => { setSubmitFor(e); setResultFor(null) }}
              onCancel={() => cancelM.mutate({ id: e.id, status: 'cancelled' })}
              onDelete={() => deleteM.mutate(e.id)}
              onReopen={() => cancelM.mutate({ id: e.id, status: 'planned' })}
              resultOpen={resultFor === e.id}
              onToggleResult={() => setResultFor(resultFor === e.id ? null : e.id)}
            />
          ))}
          {cancelled.map((e) => (
            <ExamCard
              key={e.id}
              exam={e}
              busy={cancelM.isPending || deleteM.isPending}
              onReopen={() => cancelM.mutate({ id: e.id, status: 'planned' })}
              onDelete={() => deleteM.mutate(e.id)}
              onCancel={() => undefined}
              onSubmit={() => undefined}
              onStart={() => undefined}
              onToggleResult={() => undefined}
              resultOpen={false}
            />
          ))}
        </motion.div>

        {/* --- کارنامه‌ها --- */}
        {finished.length > 0 && (
          <motion.div variants={listItem} className="space-y-3">
            <h2 className="text-title-sm font-bold">کارنامه‌ها</h2>
            {finished.map((e) => (
              <ExamCard
                key={e.id}
                exam={e}
                busy={false}
                onStart={() => undefined}
                onSubmit={() => undefined}
                onCancel={() => undefined}
                onDelete={() => undefined}
                onReopen={() => undefined}
                resultOpen={resultFor === e.id}
                onToggleResult={() => setResultFor(resultFor === e.id ? null : e.id)}
              />
            ))}
          </motion.div>
        )}
      </motion.div>

      {/* --- ثبت نتیجه (modal) --- */}
      <AnimatePresence>
        {submitFor && (
          <motion.div
            key="backdrop"
            className="fixed inset-0 z-40 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-6"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: D.fast }}
            onClick={() => setSubmitFor(null)}
          >
            <motion.div
              variants={modal} initial="initial" animate="animate" exit="exit"
              className="max-h-[88vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-surface p-5 sm:rounded-2xl"
              onClick={(ev) => ev.stopPropagation()}
            >
              <SubmitExam exam={submitFor} onClose={() => setSubmitFor(null)} onDone={invalidate} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Page>
  )
}

function MiniStat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-xl bg-surface-2 px-3 py-2.5 text-center">
      <p className={`text-title-sm font-bold tabular-nums ${tone}`}>{value}</p>
      <p className="mt-0.5 text-[11px] text-muted">{label}</p>
    </div>
  )
}

// --- فرم ثبت آزمون -------------------------------------------------------------------------

function CreateExamForm({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [title, setTitle] = useState('')
  const [kind, setKind] = useState<ExamKind>('mock')
  const [date, setDate] = useState('')       // شمسی یا میلادی — backend هر دو را قبول می‌کند
  const [minutes, setMinutes] = useState('')
  const [subjects, setSubjects] = useState('')
  const [resourceId, setResourceId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const resourcesQ = useQuery({
    queryKey: ['resources'],
    queryFn: () => api.get<{ items: BookResource[] }>('/resources'),
  })

  const createM = useMutation({
    mutationFn: (body: ExamCreateIn) => api.post<ExamOut>('/exams', body),
    onSuccess: onDone,
    onError: (e) => setError(e instanceof ApiError ? e.message : 'ثبت آزمون ناموفق بود.'),
  })

  const submit = () => {
    setError(null)
    if (!title.trim()) {
      setError('عنوان آزمون نمی‌تواند خالی باشد.')
      return
    }
    createM.mutate({
      title: title.trim(),
      kind,
      scheduled_date: date.trim() || null,
      planned_duration_minutes: minutes ? num(minutes) : null,
      subjects: subjects.split(/[،,]/).map((s) => s.trim()).filter(Boolean),
      resource_id: resourceId || null,
    })
  }

  return (
    <Card className="space-y-4 p-5">
      <div>
        <label className="mb-1 block text-body-sm font-semibold">عنوان *</label>
        <input
          value={title} onChange={(e) => setTitle(e.target.value)} placeholder="مثلاً آزمون آزمایشی ۳۰ شهریور"
          className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-body outline-none focus:border-primary"
        />
      </div>
      <div>
        <label className="mb-1 block text-body-sm font-semibold">نوع آزمون</label>
        <div className="flex flex-wrap gap-2">
          {KINDS.map((k) => (
            <button
              key={k.id} type="button" onClick={() => setKind(k.id)}
              className={`rounded-xl px-3 py-1.5 text-body-sm font-semibold transition-colors ${
                kind === k.id ? 'bg-primary text-white' : 'bg-surface-2 text-muted hover:text-ink'
              }`}
            >
              {k.fa}
            </button>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-body-sm font-semibold">تاریخ (شمسی یا میلادی)</label>
          <input
            value={date} onChange={(e) => setDate(e.target.value)} placeholder="1405/06/30" dir="ltr"
            className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-body text-left outline-none focus:border-primary"
          />
        </div>
        <div>
          <label className="mb-1 block text-body-sm font-semibold">مدت (دقیقه)</label>
          <input
            value={minutes} onChange={(e) => setMinutes(e.target.value.replace(/[^\d۰-۹]/g, ''))} placeholder="۹۰"
            inputMode="numeric"
            className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-body outline-none focus:border-primary"
          />
        </div>
      </div>
      <div>
        <label className="mb-1 block text-body-sm font-semibold">درس‌ها (با «،» جدا کن)</label>
        <input
          value={subjects} onChange={(e) => setSubjects(e.target.value)} placeholder="ریاضی، فیزیک"
          className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-body outline-none focus:border-primary"
        />
      </div>
      <div>
        <label className="mb-1 block text-body-sm font-semibold">کتاب (اختیاری)</label>
        <select
          value={resourceId} onChange={(e) => setResourceId(e.target.value)}
          className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-body outline-none focus:border-primary"
        >
          <option value="">بدون کتاب</option>
          {(resourcesQ.data?.items ?? []).map((r) => (
            <option key={r.id} value={r.id}>{r.title}</option>
          ))}
        </select>
      </div>
      {error && <p className="rounded-lg bg-danger-soft px-3 py-2 text-body-sm text-danger">{error}</p>}
      <div className="flex gap-2">
        <Button onClick={submit} disabled={createM.isPending}>{createM.isPending ? 'در حال ثبت…' : 'ثبت آزمون'}</Button>
        <Button variant="soft" onClick={onCancel}>انصراف</Button>
      </div>
    </Card>
  )
}

// --- کارت آزمون -----------------------------------------------------------------------------

interface CardProps {
  exam: ExamOut
  busy: boolean
  onStart: () => void
  onSubmit: () => void
  onCancel: () => void
  onDelete: () => void
  onReopen: () => void
  resultOpen: boolean
  onToggleResult: () => void
}

function ExamCard({ exam, busy, onStart, onSubmit, onCancel, onDelete, onReopen, resultOpen, onToggleResult }: CardProps) {
  const sc = exam.scoring
  return (
    <motion.div variants={fadeInUp}>
      <Card className="p-4 md:p-5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-title-sm font-bold">{exam.title}</h3>
              <span className={`rounded-md px-2 py-0.5 text-[11px] font-semibold ${STATUS_TONE[exam.status] ?? 'bg-surface-2'}`}>
                {exam.status_fa}
              </span>
              <span className="rounded-md bg-surface-2 px-2 py-0.5 text-[11px] text-muted">{exam.kind_fa}</span>
            </div>
            <p className="mt-1 text-body-sm text-muted">
              {exam.scheduled_date_jalali ? faDigits(exam.scheduled_date_jalali) : 'بدون تاریخ'}
              {exam.planned_duration_minutes ? ` · ${faDigits(exam.planned_duration_minutes)} دقیقه` : ''}
              {exam.resource_title ? ` · ${exam.resource_title}` : ''}
              {exam.duration_fa ? ` · زمان واقعی: ${exam.duration_fa}` : ''}
            </p>
            {exam.subjects.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {exam.subjects.map((s) => (
                  <span key={s} className="rounded-md bg-primary-soft px-1.5 py-0.5 text-[10px] font-semibold text-primary">{s}</span>
                ))}
              </div>
            )}
          </div>
          {/* scoring — دو درصد همیشه جدا (§8.1) */}
          {sc && (
            <div className="flex gap-2">
              <PercentChip label="کنکوری" value={sc.percent_konkur} tone="primary" />
              <PercentChip label="بدون جریمه" value={sc.percent_no_penalty} tone="muted" />
            </div>
          )}
        </div>

        {/* اکشن‌ها */}
        <div className="mt-3 flex flex-wrap gap-2">
          {exam.status === 'planned' && (
            <Button variant="soft" onClick={onStart} disabled={busy}>شروع آزمون</Button>
          )}
          {(exam.status === 'planned' || exam.status === 'in_progress') && (
            <>
              <Button onClick={onSubmit}>ثبت نتیجه</Button>
              <Button variant="soft" onClick={onCancel} disabled={busy}>لغو</Button>
              {exam.status === 'planned' && (
                <Button variant="ghost" onClick={onDelete} disabled={busy}>حذف</Button>
              )}
            </>
          )}
          {exam.status === 'cancelled' && (
            <>
              <Button variant="soft" onClick={onReopen} disabled={busy}>برگشت به برنامه</Button>
              <Button variant="ghost" onClick={onDelete} disabled={busy}>حذف</Button>
            </>
          )}
          {exam.status === 'finished' && (
            <Button variant="soft" onClick={onToggleResult}>{resultOpen ? 'بستن کارنامه' : 'کارنامه'}</Button>
          )}
        </div>

        {/* کارنامه */}
        <AnimatePresence>
          {resultOpen && exam.status === 'finished' && (
            <motion.div
              key="result" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }} transition={{ duration: D.normal, ease: EASE_OUT }}
              className="overflow-hidden"
            >
              <ResultBody examId={exam.id} />
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  )
}

function PercentChip({ label, value, tone }: { label: string; value: number | null; tone: 'primary' | 'muted' }) {
  const neg = value !== null && value < 0
  const cls = tone === 'primary'
    ? neg ? 'bg-danger-soft text-danger' : 'bg-primary-soft text-primary'
    : 'bg-surface-2 text-muted'
  return (
    <div className={`rounded-xl px-3 py-2 text-center ${cls}`}>
      <p className="text-title-sm font-bold tabular-nums">{pct(value)}</p>
      <p className="text-[10px]">{label}</p>
    </div>
  )
}

function ResultBody({ examId }: { examId: string }) {
  const resQ = useQuery({
    queryKey: ['exam-result', examId],
    queryFn: () => api.get<ExamResultOut>(`/exams/${examId}/result`),
  })
  if (resQ.isLoading) return <div className="flex justify-center py-4"><Spinner /></div>
  if (resQ.isError || !resQ.data) {
    return <p className="py-3 text-body-sm text-danger">{resQ.error instanceof ApiError ? resQ.error.message : 'خطا در دریافت کارنامه.'}</p>
  }
  const r = resQ.data.result
  const sc = r.scoring
  return (
    <div className="mt-4 space-y-3 border-t border-border pt-4">
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
        <CountCell label="کل" value={sc.total_count} />
        <CountCell label="درست" value={sc.correct_count} tone="text-success" />
        <CountCell label="غلط" value={sc.wrong_count} tone="text-danger" />
        <CountCell label="بی‌پاسخ" value={sc.unanswered_count} tone="text-warning" />
        <CountCell label="واردنشده" value={sc.not_entered_count} />
        <CountCell label="جریمه k" value={null} raw={faDigits(sc.penalty_k)} />
      </div>
      {r.sessions.length > 0 && (
        <div>
          <p className="mb-1 text-body-sm font-semibold">جلسه‌های این آزمون</p>
          <div className="space-y-1.5">
            {r.sessions.map((s) => (
              <div key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-surface-2 px-3 py-2 text-body-sm">
                <span>{s.resource_title ?? s.label ?? 'جلسه'}</span>
                <span className="text-muted tabular-nums">
                  {faDigits(s.correct_count ?? 0)}✓ {faDigits(s.wrong_count ?? 0)}✗ · کنکوری {pct(s.percent_konkur)} · بدون جریمه {pct(s.percent_no_penalty)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {(r.planned_topics.length > 0 || r.actual_topics.length > 0) && (
        <div className="grid gap-3 sm:grid-cols-2">
          <TopicList title="مباحث برنامه‌ریزی‌شده" topics={r.planned_topics.map((t) => t.topic_title).filter(Boolean) as string[]} />
          <TopicList title="مباحث واقعی" topics={r.actual_topics.map((t) => t.topic_title).filter(Boolean) as string[]} />
        </div>
      )}
      {r.is_mock && (
        <p className="text-[11px] text-muted">
          آزمون آزمایشی — نتایج در تحلیل و اولویت‌بندی هفته منظور می‌شود (بدون ادعای رتبه).
        </p>
      )}
    </div>
  )
}

function CountCell({ label, value, tone = 'text-ink', raw }: { label: string; value: number | null; tone?: string; raw?: string }) {
  return (
    <div className="rounded-lg bg-surface-2 px-2 py-2 text-center">
      <p className={`text-body-sm font-bold tabular-nums ${tone}`}>{raw ?? (value === null ? '—' : faDigits(value))}</p>
      <p className="text-[10px] text-muted">{label}</p>
    </div>
  )
}

function TopicList({ title, topics }: { title: string; topics: string[] }) {
  return (
    <div>
      <p className="mb-1 text-body-sm font-semibold">{title}</p>
      {topics.length === 0 ? (
        <p className="text-[11px] text-muted">—</p>
      ) : (
        <div className="flex flex-wrap gap-1">
          {topics.map((t) => (
            <span key={t} className="rounded-md bg-surface-2 px-2 py-0.5 text-[11px]">{t}</span>
          ))}
        </div>
      )}
    </div>
  )
}

// --- ثبت نتیجه (دو مسیر: جلسات / شمارش دستی) --------------------------------------------------

function SubmitExam({ exam, onClose, onDone }: { exam: ExamOut; onClose: () => void; onDone: () => void }) {
  const [tab, setTab] = useState<'sessions' | 'manual'>('sessions')
  const [picked, setPicked] = useState<string[]>([])
  const [manual, setManual] = useState({ total: '', correct: '', wrong: '', unanswered: '', minutes: '' })
  const [error, setError] = useState<string | null>(null)
  const [okMsg, setOkMsg] = useState<string | null>(null)

  const sessionsQ = useQuery({
    queryKey: ['test-sessions', 'for-exam'],
    queryFn: () => api.get<{ items: TestSessionOut[] }>('/test-sessions'),
  })
  const candidates = (sessionsQ.data?.items ?? []).filter((s) => s.finished)

  const submitM = useMutation({
    mutationFn: (body: ExamSubmitIn) => api.post<ExamOut>(`/exams/${exam.id}/submit`, body),
    onSuccess: (data) => {
      const sc = data.scoring
      setOkMsg(`ثبت شد — درصد کنکوری ${pct(sc?.percent_konkur ?? null)} · بدون جریمه ${pct(sc?.percent_no_penalty ?? null)}`)
      setError(null)
      onDone()
      setTimeout(onClose, 1400)
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'ثبت نتیجه ناموفق بود.'),
  })

  const submitSessions = () => {
    if (picked.length === 0) {
      setError('حداقل یک جلسه تست را انتخاب کن.')
      return
    }
    submitM.mutate({ session_ids: picked })
  }
  const submitManual = () => {
    const t = num(manual.total), c = num(manual.correct), w = num(manual.wrong)
    if (!manual.total || !manual.correct || !manual.wrong || Number.isNaN(t) || Number.isNaN(c) || Number.isNaN(w)) {
      setError('کل، درست و غلط الزامی است.')
      return
    }
    submitM.mutate({
      total_count: t,
      correct_count: c,
      wrong_count: w,
      unanswered_count: manual.unanswered === '' ? null : num(manual.unanswered),
      actual_duration_minutes: manual.minutes === '' ? null : num(manual.minutes),
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-title-sm font-bold">ثبت نتیجه — {exam.title}</h2>
        <button type="button" onClick={onClose} aria-label="بستن" className="rounded-md p-1 text-muted hover:text-ink">✕</button>
      </div>

      <div className="flex gap-2 rounded-xl bg-surface-2 p-1">
        {(['sessions', 'manual'] as const).map((t) => (
          <button
            key={t} type="button" onClick={() => { setTab(t); setError(null) }}
            className={`flex-1 rounded-lg px-3 py-1.5 text-body-sm font-semibold transition-colors ${
              tab === t ? 'bg-surface text-primary shadow-sm' : 'text-muted'
            }`}
          >
            {t === 'sessions' ? 'از جلسه‌های تست' : 'شمارش دستی'}
          </button>
        ))}
      </div>

      {tab === 'sessions' ? (
        <div className="space-y-2">
          {sessionsQ.isLoading && <div className="flex justify-center py-4"><Spinner /></div>}
          {candidates.length === 0 && !sessionsQ.isLoading && (
            <p className="rounded-lg bg-surface-2 px-3 py-2 text-body-sm text-muted">
              جلسه تست تمام‌شده‌ای نداری — از «شمارش دستی» استفاده کن.
            </p>
          )}
          {candidates.map((s) => (
            <label
              key={s.id}
              className={`flex cursor-pointer items-center justify-between gap-2 rounded-xl border px-3 py-2.5 text-body-sm transition-colors ${
                picked.includes(s.id) ? 'border-primary bg-primary-soft/40' : 'border-border bg-surface-2'
              }`}
            >
              <span className="flex items-center gap-2">
                <input
                  type="checkbox" checked={picked.includes(s.id)}
                  onChange={(e) => setPicked((p) => (e.target.checked ? [...p, s.id] : p.filter((x) => x !== s.id)))}
                />
                {s.resource_title ?? s.label ?? 'جلسه'}
              </span>
              <span className="text-muted tabular-nums">
                {faDigits(s.total_count)} سوال · {pct(s.percent_konkur)}
              </span>
            </label>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <NumField label="کل سوالات (T) *" value={manual.total} onChange={(v) => setManual({ ...manual, total: v })} />
          <NumField label="درست (C) *" value={manual.correct} onChange={(v) => setManual({ ...manual, correct: v })} />
          <NumField label="غلط (W) *" value={manual.wrong} onChange={(v) => setManual({ ...manual, wrong: v })} />
          <NumField label="بی‌پاسخ" value={manual.unanswered} onChange={(v) => setManual({ ...manual, unanswered: v })} />
          <NumField label="مدت واقعی (دقیقه)" value={manual.minutes} onChange={(v) => setManual({ ...manual, minutes: v })} />
          <p className="col-span-2 text-[11px] leading-5 text-muted">
            درصد کنکوری = (C − k·W) ÷ T و بدون جریمه = C ÷ T — k از تنظیمات می‌آید و هر دو درصد همیشه جدا نمایش داده می‌شوند.
          </p>
        </div>
      )}

      <AnimatePresence>
        {okMsg && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="rounded-lg bg-success-soft px-3 py-2 text-body-sm text-success">
            {okMsg}
          </motion.p>
        )}
      </AnimatePresence>
      {error && <p className="rounded-lg bg-danger-soft px-3 py-2 text-body-sm text-danger">{error}</p>}

      <div className="flex gap-2">
        <Button onClick={tab === 'sessions' ? submitSessions : submitManual} disabled={submitM.isPending}>
          {submitM.isPending ? 'در حال ثبت…' : 'ثبت نتیجه'}
        </Button>
        <Button variant="soft" onClick={onClose}>انصراف</Button>
      </div>
    </div>
  )
}

function NumField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-body-sm font-semibold">{label}</label>
      <input
        value={value} onChange={(e) => onChange(e.target.value.replace(/[^\d۰-۹]/g, ''))} inputMode="numeric"
        className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-body outline-none focus:border-primary"
      />
    </div>
  )
}
