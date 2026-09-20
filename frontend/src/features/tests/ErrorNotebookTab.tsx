/**
 * ErrorNotebookTab — دفترچه خطا، پایه (doc 04: Error Notebook | نوع اشتباه).
 * هر attempt غلط به‌صورت خودکار یک ردیف می‌گیرد؛ اینجا نوع اشتباه و یادداشت
 * دستی اضافه می‌شود (GET/PUT /tests/error-notebook).
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { ErrorNoteOut } from '../../lib/schemas'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { staggerList, listItem, fadeInUp } from '../../motion/variants'
import { ERROR_TYPES_FA, faDate } from './shared'

export function ErrorNotebookTab() {
  const qc = useQueryClient()
  const { data, isPending } = useQuery({
    queryKey: ['error-notes'],
    queryFn: () => api.get<{ items: ErrorNoteOut[] }>('/tests/error-notebook'),
  })

  if (isPending) {
    return (
      <Card className="flex justify-center p-10">
        <Spinner />
      </Card>
    )
  }

  const items = data?.items ?? []
  if (items.length === 0) {
    return (
      <EmptyState
        icon="target"
        text="دفترچه خطا خالی است — هر پاسخی که «غلط» ثبت شود خودکار اینجا می‌آید تا نوع اشتباه و درسش را بنویسی."
      />
    )
  }

  return (
    <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-3">
      <p className="px-1 text-body-sm text-muted">
        {faDigits(items.length)} اشتباه ثبت شده — نوع اشتباه را مشخص کن تا الگوهای تکراری دیده شود.
      </p>
      {items.map((n) => (
        <motion.div key={n.id} variants={listItem}>
          <NoteCard note={n} onSaved={() => qc.invalidateQueries({ queryKey: ['error-notes'] })} />
        </motion.div>
      ))}
    </motion.div>
  )
}

function NoteCard({ note, onSaved }: { note: ErrorNoteOut; onSaved: () => void }) {
  const [errorType, setErrorType] = useState(note.error_type ?? '')
  const [text, setText] = useState(note.note ?? '')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const dirty = errorType !== (note.error_type ?? '') || text !== (note.note ?? '')

  const save = async () => {
    setBusy(true)
    setMsg(null)
    try {
      await api.put(`/tests/error-notebook/${note.id}`, {
        error_type: errorType || null,
        note: text.trim() || null,
      })
      setMsg({ kind: 'ok', text: 'ذخیره شد.' })
      onSaved()
    } catch (e) {
      setMsg({ kind: 'err', text: e instanceof ApiError ? e.message : 'ذخیره نشد.' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-danger-soft text-body-sm font-bold text-danger">
            {faDigits(note.question_number ?? '?')}
          </span>
          <span className="truncate text-body-sm font-bold">{note.book_title || '—'}</span>
          <span className="truncate text-body-sm text-muted">› {note.topic_title || '—'}</span>
        </div>
        <span className="shrink-0 text-body-sm text-muted">{faDate(note.created_at)}</span>
      </div>

      <div className="flex flex-wrap gap-3 text-body-sm">
        <span className="rounded-md bg-danger-soft px-2 py-1 text-danger">
          پاسخ تو: <b>{note.your_answer || '—'}</b>
        </span>
        <span className="rounded-md bg-success-soft px-2 py-1 text-success">
          پاسخ صحیح: <b>{note.correct_answer || '—'}</b>
        </span>
      </div>

      <div className="flex flex-col gap-2 md:flex-row md:items-start">
        <select
          value={errorType}
          onChange={(e) => setErrorType(e.target.value)}
          aria-label="نوع اشتباه"
          className="rounded-md border border-border bg-surface px-2.5 py-2 text-body-sm outline-none focus:border-primary md:w-48"
        >
          <option value="">نوع اشتباه…</option>
          {ERROR_TYPES_FA.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={2}
          placeholder="چه درسی داشت؟ مثلاً: صورت سوال را دوباره بخوان…"
          aria-label="یادداشت اشتباه"
          className="min-w-0 flex-1 rounded-md border border-border bg-surface px-3 py-2 text-body-sm outline-none focus:border-primary"
        />
      </div>

      <div className="flex items-center gap-3">
        <Button variant="soft" onClick={() => void save()} disabled={!dirty || busy}>
          {busy ? <Spinner size={16} /> : null}
          ذخیره
        </Button>
        <AnimatePresence>
          {msg && (
            <motion.span
              variants={fadeInUp}
              initial="initial"
              animate="animate"
              exit="exit"
              className={['text-body-sm', msg.kind === 'ok' ? 'text-success' : 'text-danger'].join(' ')}
              role="status"
            >
              {msg.text}
            </motion.span>
          )}
        </AnimatePresence>
      </div>
    </Card>
  )
}
