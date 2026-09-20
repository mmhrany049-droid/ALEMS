/**
 * Review — صف مرور (doc 10، فاز ۴).
 * - صف از wrong/marks (+blank اختیاری) — چرخه ۱-۳-۷-۱۴ از settings
 * - critical اگر غلط ≥ ۲ (doc 08 §8.4)
 * - cluster suggestion: سقف روزانه + خوشه‌های بزرگ با هم (doc 10 §10.3)
 * - learning states per topic + weakness ترکیبی (doc 10 §10.4-10.5)
 * - لیست صف با stagger animation (doc 07.4 #2)
 */
import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type {
  ClusterSuggestionOut,
  LearningStatesOut,
  RebuildOut,
  ReviewItemOut,
  ReviewQueueOut,
} from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'
import { Icon } from '../../components/Icon'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, listItem, progressFill, staggerList } from '../../motion/variants'

const jalali = (iso: string | null) => (iso ? faDigits(iso.replace(/-/g, '/')) : '—')

function StatChip({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`flex items-center gap-2 rounded-xl px-3 py-2 ${tone}`}>
      <span className="text-title-sm font-bold tabular-nums">{faDigits(value)}</span>
      <span className="text-body-sm">{label}</span>
    </div>
  )
}

/** نقطه‌های چرخه — cycle_index از cycle_length */
function CycleDots({ item }: { item: ReviewItemOut }) {
  return (
    <span className="flex items-center gap-1" title={`چرخه ${item.cycle_index} از ${item.cycle_length}`}>
      {Array.from({ length: item.cycle_length }, (_, i) => (
        <span
          key={i}
          className={[
            'h-1.5 w-1.5 rounded-full',
            i < item.cycle_index ? 'bg-review' : 'bg-border',
          ].join(' ')}
        />
      ))}
      <span className="mr-1 text-[11px] text-muted">
        {item.cycle_index < item.cycle_length
          ? `مرور ${faDigits(item.cycle_index + 1)}${item.next_interval_days != null ? ` · بعدی +${faDigits(item.next_interval_days)} روز` : ''}`
          : 'آماده جذب'}
      </span>
    </span>
  )
}

function QueueItem({
  item,
  suggested,
  busy,
  onComplete,
  onPostpone,
}: {
  item: ReviewItemOut
  suggested: boolean
  busy: 'complete' | 'postpone' | null
  onComplete: () => void
  onPostpone: (days: number) => void
}) {
  const [days, setDays] = useState(1)
  return (
    <motion.div variants={listItem}>
      <Card
        className={[
          'p-3 transition-colors md:p-4',
          item.critical ? 'border-danger/50' : suggested ? 'border-review/50' : '',
        ].join(' ')}
      >
        <div className="flex flex-wrap items-start gap-3">
          <span
            className={[
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-body-sm font-bold',
              item.critical ? 'bg-danger-soft text-danger' : 'bg-review-soft text-review',
            ].join(' ')}
          >
            {faDigits(item.number ?? '?')}
          </span>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="truncate text-body font-semibold">{item.topic_title || '—'}</span>
              {item.book_title && (
                <span className="truncate text-body-sm text-muted">· {item.book_title}</span>
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px]">
              <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-muted">{item.source_fa}</span>
              {item.critical && (
                <span className="rounded-md bg-danger-soft px-1.5 py-0.5 font-bold text-danger">
                  بحرانی · {faDigits(item.wrong_count)} غلط
                </span>
              )}
              {!item.critical && item.wrong_count > 0 && (
                <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-muted">
                  {faDigits(item.wrong_count)} غلط
                </span>
              )}
              {item.overdue_days > 0 && (
                <span className="rounded-md bg-warning-soft px-1.5 py-0.5 font-semibold text-warning">
                  {faDigits(item.overdue_days)} روز عقب
                </span>
              )}
              {suggested && (
                <span className="rounded-md bg-review-soft px-1.5 py-0.5 font-semibold text-review">
                  پیشنهاد خوشه
                </span>
              )}
              {item.marks.review && <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-muted">تیک مرور</span>}
              {item.marks.important && <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-muted">مهم</span>}
              {item.marks.hard && <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-muted">سخت</span>}
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-body-sm text-muted">
              <CycleDots item={item} />
              <span>
                <Icon name="clock" size={12} className="ml-1 inline align-[-1px]" />
                {item.scheduled_date_jalali ? jalali(item.scheduled_date_jalali) : 'امروز'}
              </span>
              {item.correct_answer && (
                <span>
                  پاسخ تو: <b className="text-ink">{item.your_answer ?? '—'}</b> · درست:{' '}
                  <b className="text-success">{item.correct_answer}</b>
                </span>
              )}
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-1.5">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              aria-label="روزهای تأخیر"
              className="rounded-md border border-border bg-surface px-2 py-1.5 text-body-sm outline-none focus:border-primary"
            >
              {[1, 2, 3, 7].map((d) => (
                <option key={d} value={d}>
                  +{faDigits(d)} روز
                </option>
              ))}
            </select>
            <Button
              variant="ghost"
              className="!px-3 !py-1.5 text-body-sm"
              disabled={busy != null}
              onClick={() => onPostpone(days)}
              ariaLabel="تأخیر"
            >
              {busy === 'postpone' ? <Spinner size={14} /> : 'تأخیر'}
            </Button>
            <Button
              variant="soft"
              className="!px-3 !py-1.5 text-body-sm"
              disabled={busy != null}
              onClick={onComplete}
              ariaLabel="مرور شد"
            >
              {busy === 'complete' ? <Spinner size={14} /> : (
                <>
                  <Icon name="check" size={14} className="ml-1 inline align-[-2px]" />
                  مرور شد
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

function ScoreBar({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[11px] text-muted">
        <span>{label}</span>
        <span className="font-semibold tabular-nums">{faDigits(Math.round(value * 100))}٪</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
        <motion.div
          variants={progressFill}
          initial="initial"
          animate="animate"
          style={{ width: `${Math.max(2, Math.round(value * 100))}%`, transformOrigin: 'right' }}
          className={`h-full rounded-full ${tone}`}
        />
      </div>
    </div>
  )
}

export function ReviewPage() {
  const qc = useQueryClient()
  const [onlySuggested, setOnlySuggested] = useState(false)
  const [busyId, setBusyId] = useState<{ id: string; kind: 'complete' | 'postpone' } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const queue = useQuery({
    queryKey: ['reviews', 'queue'],
    queryFn: () => api.get<ReviewQueueOut>('/reviews/queue'),
  })
  const cluster = useQuery({
    queryKey: ['reviews', 'cluster'],
    queryFn: () => api.get<ClusterSuggestionOut>('/reviews/cluster-suggestion'),
  })
  const states = useQuery({
    queryKey: ['reviews', 'learning-states'],
    queryFn: () => api.get<LearningStatesOut>('/reviews/learning-states'),
  })

  const rebuild = useMutation({
    mutationFn: () => api.post<RebuildOut>('/reviews/rebuild'),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['reviews'] }),
    onError: (e) => setError(e instanceof ApiError ? e.message : 'بازسازی ناموفق بود.'),
  })

  const act = (item: ReviewItemOut, kind: 'complete' | 'postpone', days = 1) => {
    setError(null)
    setBusyId({ id: item.id, kind })
    const path = kind === 'complete' ? `/reviews/${item.id}/complete` : `/reviews/${item.id}/postpone`
    const run = kind === 'complete' ? api.post<ReviewItemOut>(path, {}) : api.post<ReviewItemOut>(path, { days })
    run
      .then(() => qc.invalidateQueries({ queryKey: ['reviews'] }))
      .catch((e) => setError(e instanceof ApiError ? e.message : 'انجام نشد؛ دوباره تلاش کن.'))
      .finally(() => setBusyId(null))
  }

  const suggestedIds = useMemo(
    () => new Set((cluster.data?.suggested ?? []).map((s) => s.id)),
    [cluster.data],
  )
  const items = useMemo(() => {
    const all = queue.data?.items ?? []
    if (!onlySuggested) return all
    return all.filter((it) => suggestedIds.has(it.id))
  }, [queue.data, onlySuggested, suggestedIds])

  const q = queue.data
  const st = states.data?.items ?? []

  return (
    <Page title="مرور" subtitle="صف مرور، چرخه ۱-۳-۷-۱۴، مرور خوشه‌ای">
      {error && (
        <p className="mb-3 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">
          {error}
        </p>
      )}

      {/* آمار + بازسازی */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: D.normal, ease: EASE_OUT }}
        className="mb-4 flex flex-wrap items-center gap-2"
      >
        <StatChip label="مرور امروز" value={q?.due_count ?? 0} tone="bg-review-soft text-review" />
        <StatChip label="پیش‌رو" value={q?.upcoming_count ?? 0} tone="bg-surface-2 text-ink" />
        <StatChip label="جذب‌شده" value={q?.absorbed_count ?? 0} tone="bg-success-soft text-success" />
        {q && (
          <span className="text-body-sm text-muted">
            چرخه: <b className="text-ink" dir="ltr">{faDigits(q.intervals.join('-'))}</b> روز
          </span>
        )}
        <div className="ms-auto">
          <Button variant="ghost" onClick={() => rebuild.mutate()} disabled={rebuild.isPending} ariaLabel="بازسازی صف">
            {rebuild.isPending ? <Spinner size={14} /> : <Icon name="sparkle" size={14} className="ml-1 inline align-[-2px]" />}
            بازسازی صف
          </Button>
        </div>
      </motion.div>

      {/* cluster suggestion (doc 10 §10.3) */}
      {cluster.data && cluster.data.clusters.length > 0 && (
        <Card className="mb-4 p-4">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-title-sm font-bold">پیشنهاد خوشه‌ای امروز</h2>
            <label className="flex cursor-pointer items-center gap-1.5 text-body-sm text-muted">
              <input
                type="checkbox"
                checked={onlySuggested}
                onChange={(e) => setOnlySuggested(e.target.checked)}
                className="accent-[var(--color-review)]"
              />
              فقط پیشنهادهای خوشه ({faDigits(cluster.data.suggested_count)})
            </label>
          </div>
          <p className="mb-3 text-body-sm text-muted">
            سقف روزانه {faDigits(cluster.data.budget)} مرور · خوشه‌های ≥ {faDigits(cluster.data.min_cluster)} با هم
          </p>
          <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-wrap gap-2">
            {cluster.data.clusters.map((c, i) => (
              <motion.div
                key={c.topic_id ?? `c${i}`}
                variants={listItem}
                className="flex items-center gap-2 rounded-xl bg-surface-2 px-3 py-2 text-body-sm"
              >
                <Icon name="target" size={14} className="text-review" />
                <span className="font-semibold">{c.topic_title || '—'}</span>
                <span className="text-muted">
                  {faDigits(c.size)} مورد
                  {c.critical_count > 0 && (
                    <b className="mr-1 text-danger">· {faDigits(c.critical_count)} بحرانی</b>
                  )}
                </span>
              </motion.div>
            ))}
          </motion.div>
        </Card>
      )}

      {/* صف مرور — stagger list (doc 07.4 #2) */}
      {queue.isPending ? (
        <div className="flex justify-center py-16">
          <Spinner size={22} />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon="review"
          text={
            (q?.due_count ?? 0) === 0
              ? 'صف مرور خالی است — بعد از هر آزمون، غلط‌ها و تیک‌ها خودکار اینجا می‌آیند.'
              : 'با این فیلتر موردی نیست؛ «فقط پیشنهادهای خوشه» را خاموش کن.'
          }
          action={
            (q?.due_count ?? 0) === 0 ? (
              <Button variant="soft" to="/tests">
                برو به آزمون‌ها
              </Button>
            ) : undefined
          }
        />
      ) : (
        <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-2">
          <AnimatePresence initial={false}>
            {items.map((it) => (
              <QueueItem
                key={it.id}
                item={it}
                suggested={suggestedIds.has(it.id)}
                busy={busyId?.id === it.id ? busyId.kind : null}
                onComplete={() => act(it, 'complete')}
                onPostpone={(d) => act(it, 'postpone', d)}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* learning states (doc 10 §10.4) */}
      {st.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-title-sm font-bold">وضعیت یادگیری موضوع‌ها</h2>
          <motion.div
            variants={staggerList}
            initial="initial"
            animate="animate"
            className="grid gap-3 md:grid-cols-2"
          >
            {st.map((s) => (
              <motion.div key={s.id} variants={listItem}>
                <Card className={['p-4', s.weakness ? 'border-danger/50' : ''].join(' ')}>
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-body font-bold">{s.topic_title}</p>
                      {s.book_title && <p className="truncate text-body-sm text-muted">{s.book_title}</p>}
                    </div>
                    {s.weakness ? (
                      <span className="shrink-0 rounded-md bg-danger-soft px-2 py-1 text-[11px] font-bold text-danger">
                        نقطه ضعف
                      </span>
                    ) : (
                      <span className="shrink-0 rounded-md bg-success-soft px-2 py-1 text-[11px] font-semibold text-success">
                        آماده‌سازی {faDigits(Math.round(s.exam_readiness * 100))}٪
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                    <ScoreBar label="پوشش" value={s.coverage} tone="bg-primary" />
                    <ScoreBar label="دقت" value={s.accuracy} tone="bg-success" />
                    <ScoreBar label="آمادگی آزمون" value={s.exam_readiness} tone="bg-review" />
                    <ScoreBar label="خطای تکراری" value={s.repeated_error_score} tone="bg-danger" />
                  </div>
                  <p className="mt-3 text-[11px] text-muted">
                    {faDigits(s.attempted_questions)} از {faDigits(s.total_questions)} سوال کار شده ·{' '}
                    {faDigits(s.correct_count)} درست / {faDigits(s.wrong_count)} غلط · اطمینان{' '}
                    {faDigits(Math.round(s.confidence * 100))}٪
                  </p>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </section>
      )}
    </Page>
  )
}
