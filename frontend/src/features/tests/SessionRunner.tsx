/**
 * SessionRunner — ثبت تست سریع (doc 09 §9.2 مرحله ۲ + §9.4 time tracking).
 * هر کلیک (درست/غلط/نزده) فوراً یک record می‌فرستد؛ تاریخچه سمت backend
 * append-only است (V2-T05) — اصلاح پاسخ = رکورد جدید، بازنویسی نمی‌شود.
 * پایان: untimed → مدت جلسه پرسیده می‌شود (پیش‌فرض از تایمر)؛ timed → همان planned.
 */
import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { FinishOut, MarksOut, ReviewMarks, SessionCreateOut, SessionQuestion } from '../../lib/schemas'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'
import { BlockTypeBadge } from '../../components/BlockTypeBadge'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, staggerList, listItem } from '../../motion/variants'
import { ScoreCard } from './ScoreCard'
import { ModeChip, fmtClock } from './shared'

type Mark = 'correct' | 'wrong' | 'blank'

export function SessionRunner({ initial, onExit }: { initial: SessionCreateOut; onExit: () => void }) {
  const session = initial.session
  const questions = initial.questions
  const [marks, setMarks] = useState<Record<string, Mark>>(() => {
    const m: Record<string, Mark> = {}
    for (const q of questions) {
      if (q.question_id && q.result && q.result !== 'unknown') {
        m[q.question_id] = q.result === 'correct' ? 'correct' : q.result === 'wrong' ? 'wrong' : 'blank'
      }
    }
    return m
  })
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [finishing, setFinishing] = useState(false)
  const [askDuration, setAskDuration] = useState(false)
  const [manualMin, setManualMin] = useState('')
  const [finished, setFinished] = useState<FinishOut | null>(null)

  // تیک‌ها (doc 04 Question Marking) — review/important/hard → صف مرور (doc 10 §10.1)
  const qc = useQueryClient()
  const [qmarks, setQmarks] = useState<Record<string, ReviewMarks>>({})
  useEffect(() => {
    let alive = true
    const ids = questions.map((q) => q.question_id).filter((x): x is string => Boolean(x))
    void Promise.all(
      ids.map((id) =>
        api
          .get<MarksOut>(`/questions/${id}/marks`)
          .then((m) => ({ id, review: m.review, important: m.important, hard: m.hard }))
          .catch(() => null),
      ),
    ).then((rows) => {
      if (!alive) return
      const next: Record<string, ReviewMarks> = {}
      for (const r of rows) if (r) next[r.id] = { review: r.review, important: r.important, hard: r.hard }
      setQmarks(next)
    })
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const toggleMark = async (q: SessionQuestion, field: keyof ReviewMarks) => {
    if (!q.question_id) return
    const qid = q.question_id
    const cur = qmarks[qid] ?? { review: false, important: false, hard: false }
    const next = { ...cur, [field]: !cur[field] }
    setQmarks((m) => ({ ...m, [qid]: next }))
    try {
      const saved = await api.put<MarksOut>(`/questions/${qid}/marks`, { [field]: next[field] })
      setQmarks((m) => ({ ...m, [qid]: { review: saved.review, important: saved.important, hard: saved.hard } }))
      void qc.invalidateQueries({ queryKey: ['reviews'] })
    } catch {
      setQmarks((m) => ({ ...m, [qid]: cur }))
      setError('تیک ثبت نشد؛ دوباره تلاش کن.')
    }
  }

  useEffect(() => {
    if (finished) return
    const t = setInterval(() => setElapsed((e) => e + 1), 1000)
    return () => clearInterval(t)
  }, [finished])

  const done = useMemo(() => Object.keys(marks).length, [marks])
  const timed = session.mode === 'timed'
  const remaining = timed && session.planned_duration ? Math.max(0, session.planned_duration - elapsed) : null

  const mark = async (q: SessionQuestion, value: Mark) => {
    if (!q.question_id) return
    setError(null)
    setPendingId(q.question_id)
    try {
      const item =
        value === 'blank'
          ? { question_id: q.question_id, status: 'unanswered' as const }
          : { question_id: q.question_id, status: 'answered' as const, result: value }
      await api.post(`/test-sessions/${session.id}/records`, { items: [item] })
      setMarks((m) => ({ ...m, [q.question_id!]: value }))
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'ثبت نشد؛ دوباره تلاش کن.')
    } finally {
      setPendingId(null)
    }
  }

  const doFinish = async () => {
    setFinishing(true)
    setError(null)
    try {
      let actual: number | undefined
      if (!timed) {
        const mins = Number(manualMin)
        actual = mins > 0 ? Math.round(mins * 60) : elapsed > 0 ? elapsed : undefined
      }
      const res = await api.post<FinishOut>(`/test-sessions/${session.id}/finish`, actual != null ? { actual_duration: actual } : {})
      setFinished(res)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'پایان جلسه ناموفق بود.')
    } finally {
      setFinishing(false)
      setAskDuration(false)
    }
  }

  if (finished) {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: D.normal, ease: EASE_OUT }} className="flex flex-col gap-4">
        <ScoreCard session={finished.session} topics={finished.topics} />
        <div className="flex flex-wrap gap-2">
          <Button onClick={onExit}>آزمون جدید</Button>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {/* هدر جلسه */}
      <Card className="sticky top-16 z-10 flex flex-wrap items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="truncate text-title-sm font-bold">{session.label || session.resource_title}</h2>
            <ModeChip mode={session.mode} />
          </div>
          <p className="mt-0.5 text-body-sm text-muted">
            {faDigits(done)} از {faDigits(session.total_count)} ثبت شده
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className={['text-title-sm font-bold tabular-nums', remaining != null && remaining < 60 ? 'text-danger' : 'text-ink'].join(' ')}>
              {remaining != null ? fmtClock(remaining) : fmtClock(elapsed)}
            </div>
            <div className="text-body-sm text-muted">{remaining != null ? 'باقی‌مانده' : 'زمان سپری‌شده'}</div>
          </div>
          <Button
            variant="soft"
            onClick={() => (timed ? void doFinish() : setAskDuration(true))}
            disabled={finishing}
          >
            {finishing ? <Spinner size={16} /> : null}
            پایان جلسه
          </Button>
        </div>
      </Card>

      {/* untimed: پرسش مدت بعد از finish (doc 09 §9.4) */}
      <AnimatePresence>
        {askDuration && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <Card className="flex flex-wrap items-center justify-between gap-3 border-primary/40 p-4">
              <p className="text-body-sm">
                چقدر طول کشید؟ (تایمر <b>{fmtClock(elapsed)}</b> را نشان می‌دهد — می‌توانی دقیقه‌ای وارد کنی)
              </p>
              <div className="flex items-center gap-2">
                <input
                  value={manualMin}
                  onChange={(e) => setManualMin(e.target.value)}
                  inputMode="numeric"
                  placeholder={String(Math.max(1, Math.round(elapsed / 60)))}
                  aria-label="مدت جلسه به دقیقه"
                  className="w-24 rounded-md border border-border bg-surface px-3 py-2 text-body-sm outline-none focus:border-primary"
                />
                <Button onClick={() => void doFinish()} disabled={finishing}>
                  {finishing ? <Spinner size={16} /> : null}
                  ثبت و پایان
                </Button>
                <Button variant="ghost" onClick={() => setAskDuration(false)}>
                  بی‌خیال
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{error}</p>
      )}

      {/* سوال‌ها — ثبت سریع */}
      <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-1.5">
        {questions.map((q, idx) => {
          const qid = q.question_id ?? `idx-${idx}`
          const m = q.question_id ? marks[q.question_id] : undefined
          const busy = pendingId === q.question_id
          return (
            <motion.div key={qid} variants={listItem}>
              <Card
                className={[
                  'flex flex-wrap items-center gap-2 p-3 transition-colors',
                  m === 'correct' ? 'border-success/40' : m === 'wrong' ? 'border-danger/40' : m === 'blank' ? 'border-warning/40' : '',
                ].join(' ')}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-2 text-body-sm font-bold text-muted">
                  {faDigits(q.number ?? idx + 1)}
                </span>
                <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
                  <span className="truncate text-body-sm font-semibold">{q.topic_title || '—'}</span>
                  {q.block_type && <BlockTypeBadge type={q.block_type} />}
                  {q.difficulty != null && (
                    <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-[11px] text-muted">
                      سختی {faDigits(q.difficulty)}
                    </span>
                  )}
                  {q.question_id && (
                    <span className="flex items-center gap-1" title="تیک‌ها — وارد صف مرور می‌شوند">
                      {(
                        [
                          { key: 'review', label: 'مرور', on: 'border-review/40 bg-review-soft text-review' },
                          { key: 'important', label: 'مهم', on: 'border-primary/40 bg-primary-soft text-primary' },
                          { key: 'hard', label: 'سخت', on: 'border-warning/40 bg-warning-soft text-warning' },
                        ] as const
                      ).map((mk) => {
                        const on = q.question_id ? (qmarks[q.question_id]?.[mk.key] ?? false) : false
                        return (
                          <button
                            key={mk.key}
                            type="button"
                            onClick={() => void toggleMark(q, mk.key)}
                            aria-pressed={on}
                            aria-label={`تیک ${mk.label}`}
                            className={[
                              'rounded-md border px-1.5 py-0.5 text-[11px] transition-colors',
                              on ? mk.on : 'border-transparent text-muted hover:bg-surface-2',
                            ].join(' ')}
                          >
                            {mk.label}
                          </button>
                        )
                      })}
                    </span>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  {(
                    [
                      { key: 'correct', label: 'درست', active: 'bg-success text-white border-success', idle: 'border-border text-success hover:bg-success-soft' },
                      { key: 'wrong', label: 'غلط', active: 'bg-danger text-white border-danger', idle: 'border-border text-danger hover:bg-danger-soft' },
                      { key: 'blank', label: 'نزده', active: 'bg-warning text-white border-warning', idle: 'border-border text-warning hover:bg-warning-soft' },
                    ] as const
                  ).map((opt) => (
                    <motion.button
                      key={opt.key}
                      whileTap={{ scale: 0.94 }}
                      transition={{ duration: D.fast }}
                      disabled={busy}
                      onClick={() => void mark(q, opt.key)}
                      aria-pressed={m === opt.key}
                      className={[
                        'rounded-md border px-3 py-1.5 text-body-sm font-semibold transition-colors disabled:opacity-50',
                        m === opt.key ? opt.active : opt.idle,
                      ].join(' ')}
                    >
                      {opt.label}
                    </motion.button>
                  ))}
                </div>
              </Card>
            </motion.div>
          )
        })}
      </motion.div>

      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onExit}>
          انصراف (جلسه در تاریخچه می‌ماند)
        </Button>
        <Button variant="soft" onClick={() => (timed ? void doFinish() : setAskDuration(true))} disabled={finishing}>
          پایان جلسه
        </Button>
      </div>
    </div>
  )
}
