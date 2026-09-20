/**
 * Study — ثبت مطالعه (doc 06, doc 16).
 * Phase 1: پنل «موضوعات آموزش‌دیده» با API واقعی (GET/PUT /students/me/taught-topics).
 *   - تا وقتی کتاب/درخت موضوعات نباشد (فاز ۲) → EmptyState.
 *   - طبق spec: mock topic id موقت نه — فقط UI آماده + API واقعی.
 * Phase 2+: session log و درخت کتاب با API واقعی جایگزین می‌شوند.
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { TaughtTopicOut } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT } from '../../motion/variants'

export function StudyPage() {
  return (
    <Page title="مطالعه" subtitle="مطالعه‌ات را ثبت کن و موضوعات آموزش‌دیده را مشخص کن">
      <div className="grid gap-4 lg:grid-cols-2">
        <TaughtTopicsPanel />
        <Card className="p-2">
          <EmptyState
            icon="book-open"
            text="فرم ثبت مطالعه در فاز بعدی — ثبت session با موضوع، نوع فعالیت (جدید/مرور) و ساعت واقعی."
          />
        </Card>
      </div>
    </Page>
  )
}

function TaughtTopicsPanel() {
  const qc = useQueryClient()
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['taught-topics'],
    queryFn: () => api.get<TaughtTopicOut[]>('/students/me/taught-topics'),
  })
  const [pending, setPending] = useState<Record<string, boolean>>({})
  const [toggleError, setToggleError] = useState<string | null>(null)

  const toggle = async (topicId: string, next: boolean) => {
    setToggleError(null)
    setPending((p) => ({ ...p, [topicId]: true }))
    try {
      // آبشاری ساده: فقط topic خود PUT می‌شود؛ cascade سمت backend (doc 08 §8.8)
      await api.put('/students/me/taught-topics', { items: [{ topic_id: topicId, taught: next }] })
      await qc.invalidateQueries({ queryKey: ['taught-topics'] })
    } catch (e) {
      setToggleError(e instanceof ApiError ? e.message : 'ذخیره نشد؛ دوباره تلاش کن.')
    } finally {
      setPending((p) => ({ ...p, [topicId]: false }))
    }
  }

  return (
    <Card className="flex flex-col p-4 md:p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-title-sm font-bold">موضوعات آموزش‌دیده</h2>
        {data && data.length > 0 && (
          <span className="text-body-sm text-muted">
            {faDigits(data.filter((t) => t.taught).length)} از {faDigits(data.length)}
          </span>
        )}
      </div>

      {isPending ? (
        <div className="flex flex-col items-center gap-3 py-8 text-muted">
          <Spinner />
          <span className="text-body-sm">در حال بارگذاری…</span>
        </div>
      ) : isError ? (
        <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">
          {error instanceof Error ? error.message : 'بارگذاری نشد.'}
        </p>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon="book"
          text="هنوز موضوعی وارد نشده — پس از وارد کردن کتاب (فاز ۲)، درخت موضوعات اینجا می‌آید و می‌توانی آموزش‌دیده/آموزش‌ندیده بگذاری."
        />
      ) : (
        <div className="flex flex-col gap-1">
          <AnimatePresence initial={false}>
            {data.map((t) => (
              <motion.div
                key={t.topic_id}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: D.fast, ease: EASE_OUT }}
                className="flex items-center justify-between gap-3 rounded-md px-2 py-2 hover:bg-surface-2"
              >
                <span className="min-w-0 flex-1 truncate text-body-sm">{t.topic_id}</span>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  transition={{ duration: D.fast }}
                  onClick={() => toggle(t.topic_id, !t.taught)}
                  disabled={!!pending[t.topic_id]}
                  className={[
                    'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-colors disabled:opacity-50',
                    t.taught ? 'border-success bg-success text-white' : 'border-border bg-surface text-transparent',
                  ].join(' ')}
                  aria-label={t.taught ? 'آموزش‌دیده نیست' : 'آموزش‌دیده است'}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M4 12.5 9.5 18 20 6.5" />
                  </svg>
                </motion.button>
              </motion.div>
            ))}
          </AnimatePresence>
          {toggleError && (
            <p className="mt-2 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">{toggleError}</p>
          )}
        </div>
      )}
    </Card>
  )
}
