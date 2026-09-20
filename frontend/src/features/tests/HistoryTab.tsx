/**
 * HistoryTab — تاریخچه جلسات + جزئیات (append-only: تاریخچه کامل attemptها
 * در پاسخ هست؛ V2-T05). درصد کنکوری و شمارش‌ها جدا نمایش داده می‌شوند.
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type { SessionCreateOut, SessionDetailOut, TestSessionOut } from '../../lib/schemas'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, staggerList, listItem } from '../../motion/variants'
import { ScoreCard } from './ScoreCard'
import { ModeChip, ResultChip, faDate, fmtPercent } from './shared'

export function HistoryTab({ onNew, onResume }: { onNew: () => void; onResume?: (s: SessionCreateOut) => void }) {
  const [selected, setSelected] = useState<string | null>(null)
  const list = useQuery({
    queryKey: ['test-sessions'],
    queryFn: () => api.get<{ items: TestSessionOut[] }>('/test-sessions'),
  })
  const detail = useQuery({
    queryKey: ['test-session', selected],
    enabled: !!selected,
    queryFn: () => api.get<SessionDetailOut>(`/test-sessions/${selected}`),
  })

  if (list.isPending) {
    return (
      <Card className="flex justify-center p-10">
        <Spinner />
      </Card>
    )
  }

  const items = list.data?.items ?? []
  if (items.length === 0) {
    return (
      <EmptyState
        icon="test"
        text="هنوز جلسه آزمونی نداری — اولین آزمون را با انتخاب بازه و زوج/فرد بساز."
        action={<Button onClick={onNew}>آزمون جدید</Button>}
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-2">
        {items.map((s) => (
          <motion.div key={s.id} variants={listItem}>
            <motion.button
              whileTap={{ scale: 0.985 }}
              transition={{ duration: D.fast }}
              onClick={() => setSelected(s.id === selected ? null : s.id)}
              aria-expanded={s.id === selected}
              className={[
                'flex w-full items-center justify-between gap-3 rounded-lg border p-3.5 text-right transition-colors',
                s.id === selected ? 'border-primary bg-primary-soft' : 'border-border bg-surface hover:bg-surface-2',
              ].join(' ')}
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="truncate text-body font-bold">{s.label || s.resource_title || 'جلسه'}</span>
                  <ModeChip mode={s.mode} />
                  {!s.finished && (
                    <span className="rounded-md bg-warning-soft px-1.5 py-0.5 text-[11px] font-semibold text-warning">
                      ناتمام
                    </span>
                  )}
                </div>
                <div className="mt-1 text-body-sm text-muted">
                  {faDate(s.started_at)} · {faDigits(s.total_count)} سوال
                  {s.finished && ` · ${faDigits(s.correct_count)}✓ ${faDigits(s.wrong_count)}✗`}
                </div>
              </div>
              {s.finished && (
                <span className={['shrink-0 text-title-sm font-bold', (s.percent_konkur ?? 0) < 0 ? 'text-danger' : 'text-primary'].join(' ')}>
                  {fmtPercent(s.percent_konkur)}
                </span>
              )}
            </motion.button>
          </motion.div>
        ))}
      </motion.div>

      <AnimatePresence mode="wait">
        {selected && (
          <motion.div
            key={selected}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: D.normal, ease: EASE_OUT }}
            className="flex flex-col gap-3"
          >
            {detail.isPending ? (
              <Card className="flex justify-center p-8">
                <Spinner />
              </Card>
            ) : detail.data ? (
              <>
                {!detail.data.session.finished && onResume && (
                  <div className="flex items-center justify-between gap-3 rounded-lg border border-warning/40 bg-warning-soft p-3">
                    <p className="text-body-sm font-semibold text-warning">این جلسه ناتمام است — می‌توانی ادامه‌اش بدهی.</p>
                    <Button
                      onClick={() =>
                        onResume({ session: detail.data!.session, questions: detail.data!.questions })
                      }
                    >
                      ادامه جلسه
                    </Button>
                  </div>
                )}
                <ScoreCard session={detail.data.session} topics={detail.data.topics} />
                <Card className="p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-body-sm font-bold">سوال‌ها</h3>
                    <span className="text-body-sm text-muted" title="تاریخچه attemptها append-only است">
                      تاریخچه: {faDigits(detail.data.attempts.length)} ردیف
                    </span>
                  </div>
                  <div className="flex max-h-80 flex-col gap-0.5 overflow-y-auto pl-1">
                    {detail.data.questions.map((q, i) => (
                      <div key={q.question_id ?? i} className="flex items-center gap-2 rounded-md px-2 py-1.5 text-body-sm hover:bg-surface-2">
                        <span className="w-8 shrink-0 text-muted">{faDigits(q.number ?? i + 1)}.</span>
                        <span className="min-w-0 flex-1 truncate text-muted">{q.topic_title || '—'}</span>
                        {detail.data.session.finished && q.correct_answer && (
                          <span className="shrink-0 text-body-sm text-muted">
                            تو: <b className="text-ink">{q.answer || '—'}</b> · کلید: <b className="text-ink">{q.correct_answer}</b>
                          </span>
                        )}
                        <ResultChip result={q.result} />
                      </div>
                    ))}
                  </div>
                </Card>
              </>
            ) : null}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
