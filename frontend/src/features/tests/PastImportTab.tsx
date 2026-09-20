/**
 * PastImportTab — نتایج قدیمی با not_entered (doc 09 §9.3، V2-T03).
 * همان آزمون را دوباره import کن: «تکمیل بعدی همان attempt را به answered
 * تبدیل می‌کند (نه duplicate)» — ردیف جدید ساخته نمی‌شود، درصد به‌روز می‌شود.
 * نکته: کتاب TOC-only هم OK است — سوال‌های نبود با شماره+کلید ساخته می‌شوند.
 */
import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { api, ApiError } from '../../lib/api'
import type { PastImportOut } from '../../lib/schemas'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, staggerList, listItem } from '../../motion/variants'
import { ScoreCard } from './ScoreCard'
import { flattenTree, useBooks, useTree } from './shared'

type PastStatus = 'answered' | 'unanswered' | 'not_entered'

interface Row {
  number: string
  status: PastStatus
  result: '' | 'correct' | 'wrong'
  answer: string
  correct_answer: string
}

const emptyRow = (): Row => ({ number: '', status: 'answered', result: '', answer: '', correct_answer: '' })

const inputCls =
  'rounded-md border border-border bg-surface px-2.5 py-1.5 text-body-sm text-ink outline-none transition-colors focus:border-primary'

export function PastImportTab() {
  const books = useBooks()
  const [bookId, setBookId] = useState('')
  const tree = useTree(bookId || null)
  const [topicId, setTopicId] = useState('')
  const [label, setLabel] = useState('')
  const [rows, setRows] = useState<Row[]>([emptyRow(), emptyRow()])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PastImportOut | null>(null)

  const flatTopics = useMemo(() => (tree.data ? flattenTree(tree.data.tree) : []), [tree.data])

  const setRow = (i: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)))

  const submit = async () => {
    setBusy(true)
    setError(null)
    try {
      const items = rows
        .filter((r) => r.number.trim() !== '')
        .map((r) => {
          const item: Record<string, unknown> = { number: Number(r.number), status: r.status }
          if (r.status === 'answered') {
            if (r.result) item.result = r.result
            if (r.answer.trim()) item.answer = r.answer.trim()
          }
          if (r.correct_answer.trim()) item.correct_answer = r.correct_answer.trim()
          return item
        })
      if (items.length === 0) {
        setError('حداقل یک ردیف با شماره سوال وارد کن.')
        return
      }
      const res = await api.post<PastImportOut>('/tests/past-import', {
        resource_id: bookId,
        topic_id: topicId,
        label: label.trim() || undefined,
        items,
      })
      setResult(res)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'ثبت نتایج قدیمی ناموفق بود.')
    } finally {
      setBusy(false)
    }
  }

  if (books.isPending) {
    return (
      <Card className="flex justify-center p-10">
        <Spinner />
      </Card>
    )
  }
  const bookItems = books.data?.items ?? []
  if (bookItems.length === 0) {
    return (
      <EmptyState
        icon="book"
        text="اول یک کتاب وارد کن — حتی فقط فهرست (TOC-only) کافی است؛ سوال‌های آزمون قدیمی موقع import ساخته می‌شوند."
        action={<Button to="/import">وارد کردن کتاب</Button>}
      />
    )
  }

  const canSubmit = !!bookId && !!topicId && rows.some((r) => r.number.trim() !== '')

  return (
    <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-4">
      <AnimatePresence>
        {result && (
          <motion.div key="result" variants={listItem} initial="initial" animate="animate" exit="exit">
            <Card className="flex flex-col gap-3 border-success/40 p-4">
              <p className="text-body-sm">
                <b className="text-success">ثبت شد:</b> {faDigits(result.imported)} ردیف جدید ·{' '}
                {faDigits(result.updated)} ردیف تکمیل/به‌روز شد
                {result.created_questions > 0 && <> · {faDigits(result.created_questions)} سوال ساخته شد</>}
                {result.created_answer_keys > 0 && <> · {faDigits(result.created_answer_keys)} کلید پاسخ</>}
              </p>
              <p className="text-body-sm text-muted">
                وارد کردن دوبارهٔ همان شماره‌ها در همان آزمون، «همان attempt» را کامل می‌کند — ردیف تکراری ساخته نمی‌شود.
              </p>
              <ScoreCard session={result.session} />
              <div>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setResult(null)
                    setRows([emptyRow(), emptyRow()])
                  }}
                >
                  import بعدی
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div variants={listItem}>
        <Card className="flex flex-col gap-3 p-4">
          <h2 className="text-title-sm font-bold">۱. آزمون قدیمی</h2>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-1 text-body-sm text-muted">
              کتاب
              <select
                value={bookId}
                onChange={(e) => {
                  setBookId(e.target.value)
                  setTopicId('')
                }}
                className={inputCls}
              >
                <option value="">انتخاب کن…</option>
                {bookItems.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.title}
                    {b.publisher ? ` — ${b.publisher}` : ''}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-body-sm text-muted">
              موضوع
              <select value={topicId} onChange={(e) => setTopicId(e.target.value)} className={inputCls} disabled={!bookId}>
                <option value="">انتخاب کن…</option>
                {flatTopics.map(({ node, depth }) => (
                  <option key={node.id} value={node.id}>
                    {'— '.repeat(depth)}
                    {node.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-body-sm text-muted md:col-span-2">
              برچسب آزمون (برای شناسایی آزمونِ همان ردیف‌ها در import مجدد)
              <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="مثلاً: کنکور ۱۴۰۲ داخل"
                className={inputCls}
              />
            </label>
          </div>
        </Card>
      </motion.div>

      <motion.div variants={listItem}>
        <Card className="flex flex-col gap-3 p-4">
          <h2 className="text-title-sm font-bold">۲. ردیف‌های نتیجه</h2>
          <p className="text-body-sm text-muted">
            وضعیت «وارد نشده» یعنی نتیجه‌اش را هنوز پیدا نکرده‌ای — بعداً با import دوباره کاملش کن.
          </p>
          <div className="flex flex-col gap-2">
            {rows.map((r, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: D.fast, ease: EASE_OUT }}
                className="grid grid-cols-2 items-center gap-2 rounded-md bg-surface-2/50 p-2 md:grid-cols-[64px_130px_120px_1fr_1fr_36px]"
              >
                <input
                  value={r.number}
                  onChange={(e) => setRow(i, { number: e.target.value })}
                  inputMode="numeric"
                  placeholder="شماره"
                  aria-label={`شماره سوال ردیف ${i + 1}`}
                  className={inputCls}
                />
                <select
                  value={r.status}
                  onChange={(e) => setRow(i, { status: e.target.value as PastStatus })}
                  aria-label={`وضعیت ردیف ${i + 1}`}
                  className={inputCls}
                >
                  <option value="answered">پاسخ داده</option>
                  <option value="unanswered">نزده</option>
                  <option value="not_entered">وارد نشده</option>
                </select>
                <select
                  value={r.result}
                  onChange={(e) => setRow(i, { result: e.target.value as Row['result'] })}
                  disabled={r.status !== 'answered'}
                  aria-label={`نتیجه ردیف ${i + 1}`}
                  className={inputCls}
                >
                  <option value="">خودکار (از کلید)</option>
                  <option value="correct">درست</option>
                  <option value="wrong">غلط</option>
                </select>
                <input
                  value={r.answer}
                  onChange={(e) => setRow(i, { answer: e.target.value })}
                  disabled={r.status !== 'answered'}
                  placeholder="پاسخ تو"
                  aria-label={`پاسخ تو ردیف ${i + 1}`}
                  className={inputCls}
                />
                <input
                  value={r.correct_answer}
                  onChange={(e) => setRow(i, { correct_answer: e.target.value })}
                  placeholder="پاسخ صحیح (کلید)"
                  aria-label={`پاسخ صحیح ردیف ${i + 1}`}
                  className={inputCls}
                />
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setRows((rs) => rs.filter((_, j) => j !== i))}
                  disabled={rows.length <= 1}
                  aria-label={`حذف ردیف ${i + 1}`}
                  className="flex h-8 w-8 items-center justify-center rounded-md text-muted hover:bg-danger-soft hover:text-danger disabled:opacity-40"
                >
                  ✕
                </motion.button>
              </motion.div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="ghost" onClick={() => setRows((rs) => [...rs, emptyRow()])}>
              + ردیف جدید
            </Button>
            <Button onClick={() => void submit()} disabled={!canSubmit || busy}>
              {busy && <Spinner size={16} />}
              ثبت نتایج قدیمی
            </Button>
          </div>
          {error && (
            <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{error}</p>
          )}
        </Card>
      </motion.div>

      <motion.p variants={listItem} className="px-1 text-body-sm text-muted">
        تعداد ردیف وارد شده: {faDigits(rows.filter((r) => r.number.trim() !== '').length)}
      </motion.p>
    </motion.div>
  )
}
