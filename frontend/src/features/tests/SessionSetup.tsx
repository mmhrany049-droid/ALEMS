/**
 * SessionSetup — ساخت جلسه آزمون (doc 09 §9.2).
 * انتخاب: کتاب → موضوعات (فصل = همه نوادگان) → range (from/to) + parity + count + difficulty
 * preview زنده از GET /test-engine/preview؛ اگر سوالی نماند پیام فارسی سند نشان داده می‌شود.
 */
import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { PreviewOut, SessionCreateOut, SessionMode } from '../../lib/schemas'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { BlockTypeBadge } from '../../components/BlockTypeBadge'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, fadeInUp, staggerList, listItem } from '../../motion/variants'
import { PARITY_LABELS_FA, flattenTree, useBooks, useTree } from './shared'

const inputCls =
  'w-full rounded-md border border-border bg-surface px-3 py-2 text-body-sm text-ink outline-none transition-colors focus:border-primary'

export function SessionSetup({ onStart }: { onStart: (data: SessionCreateOut) => void }) {
  const books = useBooks()
  const [bookId, setBookId] = useState('')
  const tree = useTree(bookId || null)
  const [topicIds, setTopicIds] = useState<Set<string>>(new Set())
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [parity, setParity] = useState<'any' | 'odd' | 'even'>('any')
  const [count, setCount] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [mode, setMode] = useState<SessionMode>('untimed')
  const [plannedMin, setPlannedMin] = useState('')
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const flatTopics = useMemo(() => (tree.data ? flattenTree(tree.data.tree) : []), [tree.data])

  const previewParams = useMemo(() => {
    if (!bookId) return null
    const p = new URLSearchParams({ resource_id: bookId, parity })
    if (topicIds.size > 0) p.set('topic_ids', [...topicIds].join(','))
    if (from.trim()) p.set('from', from.trim())
    if (to.trim()) p.set('to', to.trim())
    if (count.trim()) p.set('count', count.trim())
    if (difficulty) p.set('difficulty', difficulty)
    return p.toString()
  }, [bookId, topicIds, from, to, parity, count, difficulty])

  const preview = useQuery({
    queryKey: ['preview', previewParams],
    enabled: !!previewParams,
    queryFn: () => api.get<PreviewOut>(`/test-engine/preview?${previewParams}`),
  })

  const toggleTopic = (id: string) => {
    setTopicIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const start = async () => {
    setBusy(true)
    setError(null)
    try {
      const body: Record<string, unknown> = {
        mode,
        resource_id: bookId,
        topic_ids: [...topicIds],
        parity,
        label: label.trim() || undefined,
      }
      if (from.trim()) body.from_number = Number(from)
      if (to.trim()) body.to_number = Number(to)
      if (count.trim()) body.count = Number(count)
      if (difficulty) body.difficulty = Number(difficulty)
      if (mode === 'timed') body.planned_duration = Math.max(1, Math.round(Number(plannedMin || 0) * 60))
      const data = await api.post<SessionCreateOut>('/test-sessions', body)
      onStart(data)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'جلسه ساخته نشد؛ دوباره تلاش کن.')
    } finally {
      setBusy(false)
    }
  }

  if (books.isPending) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-muted">
        <Spinner />
      </Card>
    )
  }

  const bookItems = books.data?.items ?? []
  if (bookItems.length === 0) {
    return (
      <EmptyState
        icon="book"
        text="برای ساخت آزمون اول به یک کتاب با سوال نیاز داری. فهرست کتاب را وارد کن؛ سوال‌ها را می‌توانی بعداً با «نتایج قدیمی» اضافه کنی."
        action={<Button to="/import">وارد کردن کتاب</Button>}
      />
    )
  }

  const canStart = !!bookId && (preview.data?.matching ?? 0) > 0 && (mode === 'untimed' || Number(plannedMin) > 0)

  return (
    <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-4">
      {/* انتخاب کتاب */}
      <motion.div variants={listItem}>
        <Card className="flex flex-col gap-3 p-4">
          <h2 className="text-title-sm font-bold">۱. کتاب</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {bookItems.map((b) => (
              <motion.button
                key={b.id}
                whileTap={{ scale: 0.985 }}
                transition={{ duration: D.fast }}
                onClick={() => {
                  setBookId(b.id)
                  setTopicIds(new Set())
                }}
                className={[
                  'rounded-md border p-3 text-right transition-colors',
                  b.id === bookId ? 'border-primary bg-primary-soft' : 'border-border bg-surface hover:bg-surface-2',
                ].join(' ')}
              >
                <div className="text-body font-bold">{b.title}</div>
                <div className="mt-0.5 text-body-sm text-muted">
                  {b.publisher && `${b.publisher} · `}{faDigits(b.counts.questions)} سوال
                </div>
              </motion.button>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* انتخاب موضوع */}
      {bookId && (
        <motion.div variants={listItem}>
          <Card className="flex flex-col gap-3 p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-title-sm font-bold">۲. موضوعات (اختیاری)</h2>
              {topicIds.size > 0 && (
                <button onClick={() => setTopicIds(new Set())} className="text-body-sm text-primary hover:underline">
                  پاک کردن انتخاب
                </button>
              )}
            </div>
            <p className="text-body-sm text-muted">
              هیچ‌کدام = کل کتاب · انتخاب فصل یعنی همه زیرموضوع‌هایش
            </p>
            {tree.isPending ? (
              <Spinner />
            ) : (
              <div className="flex max-h-56 flex-col gap-0.5 overflow-y-auto pl-1">
                {flatTopics.map(({ node, depth }) => (
                  <label
                    key={node.id}
                    className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-body-sm hover:bg-surface-2"
                    style={{ paddingInlineStart: 8 + depth * 18 }}
                  >
                    <input
                      type="checkbox"
                      checked={topicIds.has(node.id)}
                      onChange={() => toggleTopic(node.id)}
                      className="h-4 w-4 accent-[var(--color-primary)]"
                    />
                    <span className={['min-w-0 flex-1 truncate', node.is_structural ? 'font-bold' : ''].join(' ')}>
                      {node.title}
                    </span>
                    {node.question_count > 0 && (
                      <span className="shrink-0 text-body-sm text-muted">{faDigits(node.question_count)} سوال</span>
                    )}
                    <BlockTypeBadge type={node.block_type} label={node.block_type_fa} />
                  </label>
                ))}
              </div>
            )}
          </Card>
        </motion.div>
      )}

      {/* فیلترها */}
      {bookId && (
        <motion.div variants={listItem}>
          <Card className="flex flex-col gap-4 p-4">
            <h2 className="text-title-sm font-bold">۳. بازه و فیلتر</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <label className="flex flex-col gap-1 text-body-sm text-muted">
                از شماره
                <input value={from} onChange={(e) => setFrom(e.target.value)} inputMode="numeric" placeholder="۱" className={inputCls} />
              </label>
              <label className="flex flex-col gap-1 text-body-sm text-muted">
                تا شماره
                <input value={to} onChange={(e) => setTo(e.target.value)} inputMode="numeric" placeholder="۱۰" className={inputCls} />
              </label>
              <label className="flex flex-col gap-1 text-body-sm text-muted">
                زوج/فرد
                <select value={parity} onChange={(e) => setParity(e.target.value as 'any' | 'odd' | 'even')} className={inputCls}>
                  {(Object.keys(PARITY_LABELS_FA) as ('any' | 'odd' | 'even')[]).map((p) => (
                    <option key={p} value={p}>{PARITY_LABELS_FA[p]}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1 text-body-sm text-muted">
                تعداد (اختیاری)
                <input value={count} onChange={(e) => setCount(e.target.value)} inputMode="numeric" placeholder="همه" className={inputCls} />
              </label>
              <label className="flex flex-col gap-1 text-body-sm text-muted">
                سختی (اختیاری)
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className={inputCls}>
                  <option value="">همه</option>
                  {[1, 2, 3, 4, 5].map((d) => (
                    <option key={d} value={d}>{faDigits(d)}</option>
                  ))}
                </select>
              </label>
            </div>

            {/* preview زنده */}
            {preview.data && (
              <motion.div variants={fadeInUp} initial="initial" animate="animate" className="rounded-md border border-border bg-surface-2/50 p-3">
                {preview.data.matching > 0 ? (
                  <>
                    <p className="text-body-sm font-bold">
                      <span className="text-primary">{faDigits(preview.data.matching)}</span> سوال با این شرایط
                      {preview.data.matching !== preview.data.available_in_scope && (
                        <span className="font-normal text-muted"> (از {faDigits(preview.data.available_in_scope)} سوال موجود)</span>
                      )}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {preview.data.numbers.slice(0, 40).map((n) => (
                        <span key={n} className="rounded-md bg-surface px-1.5 py-0.5 text-body-sm text-muted">
                          {faDigits(n)}
                        </span>
                      ))}
                      {preview.data.numbers.length > 40 && <span className="text-body-sm text-muted">…</span>}
                    </div>
                  </>
                ) : (
                  <p className="text-body-sm font-semibold text-warning" role="status">
                    {preview.data.message}
                  </p>
                )}
              </motion.div>
            )}
          </Card>
        </motion.div>
      )}

      {/* حالت + شروع */}
      {bookId && (
        <motion.div variants={listItem}>
          <Card className="flex flex-col gap-4 p-4">
            <h2 className="text-title-sm font-bold">۴. حالت جلسه</h2>
            <div className="flex flex-wrap gap-2">
              {(['untimed', 'timed'] as const).map((m) => (
                <motion.button
                  key={m}
                  whileTap={{ scale: 0.97 }}
                  transition={{ duration: D.fast, ease: EASE_OUT }}
                  onClick={() => setMode(m)}
                  className={[
                    'rounded-md border px-4 py-2 text-body-sm font-semibold transition-colors',
                    mode === m ? 'border-primary bg-primary-soft text-primary' : 'border-border bg-surface text-muted hover:bg-surface-2',
                  ].join(' ')}
                >
                  {m === 'timed' ? 'زمان‌دار' : 'بدون زمان'}
                </motion.button>
              ))}
              {mode === 'timed' && (
                <label className="flex items-center gap-2 text-body-sm text-muted">
                  مدت (دقیقه)
                  <input
                    value={plannedMin}
                    onChange={(e) => setPlannedMin(e.target.value)}
                    inputMode="numeric"
                    placeholder="۳۰"
                    className={`${inputCls} !w-24`}
                  />
                </label>
              )}
            </div>
            <label className="flex flex-col gap-1 text-body-sm text-muted">
              برچسب جلسه (اختیاری)
              <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="مثلاً مرور شب آزمون" className={inputCls} />
            </label>

            {error && (
              <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{error}</p>
            )}

            <div className="flex justify-start">
              <Button onClick={() => void start()} disabled={!canStart || busy}>
                {busy && <Spinner size={16} />}
                شروع آزمون
              </Button>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  )
}
