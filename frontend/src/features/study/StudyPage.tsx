/**
 * Study — کتاب‌ها، درخت موضوعات و وضعیت آموزش‌دیده (فاز ۲، doc 08 §8.8 + doc 09).
 *
 * - GET /resources → فهرست کتاب‌ها (بدون کتاب → EmptyState با CTA به /import)
 * - GET /resources/{id}/tree → درخت با badge نوع بلوک + شمار سوال + taught
 * - taught toggle → PUT /students/me/taught-topics (cascade parent→child سمت backend؛
 *   parent می‌تواند «قسمتی» بماند — doc 08 §8.8)
 * - ثبت مطالعه (session log) در فاز بعدی با API واقعی می‌آید.
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { BookResource, TreeOut, TreeNode } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { BlockTypeBadge } from '../../components/BlockTypeBadge'
import { Icon } from '../../components/Icon'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, staggerList, listItem } from '../../motion/variants'

export function StudyPage() {
  return (
    <Page title="مطالعه" subtitle="کتاب‌ها، درخت موضوعات و وضعیت آموزش‌دیده">
      <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
        <BooksPanel />
        <div className="flex flex-col gap-4">
          <Card className="p-2">
            <EmptyState
              icon="book-open"
              text="فرم ثبت مطالعه در فاز بعدی — ثبت session با موضوع، نوع فعالیت (جدید/مرور) و ساعت واقعی."
            />
          </Card>
        </div>
      </div>
    </Page>
  )
}

// --- books list ---------------------------------------------------------------

function BooksPanel() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['resources'],
    queryFn: () => api.get<{ items: BookResource[] }>('/resources'),
  })

  if (isPending) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-muted">
        <Spinner />
        <span className="text-body-sm">در حال بارگذاری کتاب‌ها…</span>
      </Card>
    )
  }

  if (isError) {
    return (
      <Card className="p-4">
        <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">
          {error instanceof Error ? error.message : 'بارگذاری کتاب‌ها ناموفق بود.'}
        </p>
      </Card>
    )
  }

  const items = data?.items ?? []

  if (items.length === 0) {
    return (
      <EmptyState
        icon="book"
        text="هنوز کتابی وارد نکرده‌ای. فقط با فهرست کتاب (بدون هیچ سوال) هم می‌شود وارد کرد — درخت موضوعات و وضعیت آموزش‌دیده از همان ساخته می‌شود."
        action={<Button to="/import">وارد کردن کتاب</Button>}
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-2">
        {items.map((book) => (
          <motion.div key={book.id} variants={listItem}>
            <BookRow book={book} selected={book.id === selectedId} onToggle={() => setSelectedId(book.id === selectedId ? null : book.id)} />
          </motion.div>
        ))}
      </motion.div>

      <AnimatePresence mode="wait">
        {selectedId && (
          <motion.div key={selectedId} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: D.normal, ease: EASE_OUT }}>
            <BookTreeCard resourceId={selectedId} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex justify-end">
        <Button variant="soft" to="/import">
          <Icon name="book-open" size={16} />
          وارد کردن کتاب دیگر
        </Button>
      </div>
    </div>
  )
}

function BookRow({ book, selected, onToggle }: { book: BookResource; selected: boolean; onToggle: () => void }) {
  return (
    <motion.button
      whileTap={{ scale: 0.985 }}
      transition={{ duration: D.fast }}
      onClick={onToggle}
      aria-expanded={selected}
      className={[
        'flex w-full items-center justify-between gap-3 rounded-lg border p-3.5 text-right transition-colors',
        selected ? 'border-primary bg-primary-soft' : 'border-border bg-surface hover:bg-surface-2',
      ].join(' ')}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="truncate text-body font-bold">{book.title}</span>
          {book.subject && <span className="shrink-0 rounded-md bg-surface-2 px-1.5 py-0.5 text-body-sm text-muted">{book.subject}</span>}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-body-sm text-muted">
          {book.publisher && <span>{book.publisher}</span>}
          <span>·</span>
          <span>{faDigits(book.counts.chapters)} فصل</span>
          <span>·</span>
          <span>{faDigits(book.counts.topics)} موضوع</span>
          <span>·</span>
          <span>{book.counts.questions > 0 ? `${faDigits(book.counts.questions)} سوال` : 'فقط فهرست'}</span>
        </div>
      </div>
      <motion.span animate={{ rotate: selected ? 90 : 0 }} transition={{ duration: D.fast, ease: EASE_OUT }} className="shrink-0 text-muted" style={{ transform: 'scaleX(-1)' }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="m9 6 6 6-6 6" />
        </svg>
      </motion.span>
    </motion.button>
  )
}

// --- tree ---------------------------------------------------------------------

function BookTreeCard({ resourceId }: { resourceId: string }) {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['resource-tree', resourceId],
    queryFn: () => api.get<TreeOut>(`/resources/${resourceId}/tree`),
  })

  return (
    <Card className="p-4 md:p-5">
      {isPending ? (
        <div className="flex flex-col items-center gap-3 py-8 text-muted">
          <Spinner />
          <span className="text-body-sm">در حال بارگذاری درخت…</span>
        </div>
      ) : isError ? (
        <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger" role="alert">
          {error instanceof Error ? error.message : 'درخت بارگذاری نشد.'}
        </p>
      ) : data && data.tree.length === 0 ? (
        <EmptyState icon="book-open" text="این کتاب هیچ فصل یا موضوعی ندارد — می‌توانی از صفحه وارد کردن، نسخه کامل‌ترش را جایگزین کنی." />
      ) : data ? (
        <>
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="text-title-sm font-bold">درخت «{data.resource.title}»</h2>
            <TaughtSummary tree={data.tree} />
          </div>
          <div className="flex flex-col" role="tree" aria-label={`درخت موضوعات ${data.resource.title}`}>
            {data.tree.map((node) => (
              <TopicRow key={node.id} node={node} depth={0} />
            ))}
          </div>
        </>
      ) : null}
    </Card>
  )
}

function TaughtSummary({ tree }: { tree: TreeNode[] }) {
  let taught = 0
  let total = 0
  const walk = (n: TreeNode) => {
    if (!n.is_structural) {
      total += 1
      if (n.taught) taught += 1
    }
    n.children.forEach(walk)
  }
  tree.forEach(walk)
  if (total === 0) return null
  return (
    <span className="shrink-0 text-body-sm text-muted">
      <span className={taught > 0 ? 'font-bold text-success' : ''}>{faDigits(taught)}</span> از {faDigits(total)} آموزش‌دیده
    </span>
  )
}

function TopicRow({ node, depth }: { node: TreeNode; depth: number }) {
  const [open, setOpen] = useState(depth === 0)
  const qc = useQueryClient()
  const [pending, setPending] = useState(false)
  const [toggleError, setToggleError] = useState<string | null>(null)
  const hasChildren = node.children.length > 0

  const toggleTaught = async (next: boolean) => {
    setToggleError(null)
    setPending(true)
    try {
      await api.put('/students/me/taught-topics', { items: [{ topic_id: node.id, taught: next }] })
      // cascade سمت backend اعمال شد → درخت را تازه کن تا فرزندان/والد به‌روز دیده شوند
      await qc.invalidateQueries({ queryKey: ['resource-tree'] })
    } catch (e) {
      setToggleError(e instanceof ApiError ? e.message : 'ذخیره نشد؛ دوباره تلاش کن.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div role="treeitem" aria-expanded={hasChildren ? open : undefined} aria-selected={node.taught}>
      <div
        className="flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors hover:bg-surface-2"
        style={{ paddingInlineStart: 8 + depth * 20 }}
      >
        {hasChildren ? (
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setOpen((o) => !o)}
            aria-label={open ? 'بستن' : 'باز کردن'}
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted hover:text-ink"
          >
            <motion.span animate={{ rotate: open ? -90 : 0 }} transition={{ duration: D.fast, ease: EASE_OUT }} className="inline-flex">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="m6 9 6 6 6-6" />
              </svg>
            </motion.span>
          </motion.button>
        ) : (
          <span className="h-6 w-6 shrink-0" />
        )}

        <span className={['min-w-0 flex-1 truncate text-body-sm', node.is_structural ? 'font-bold' : ''].join(' ')}>
          {node.title}
        </span>

        {node.taught_state === 'partial' && (
          <span className="shrink-0 rounded-md bg-warning-soft px-1.5 py-0.5 text-[11px] font-semibold leading-4 text-warning" title="قسمتی از زیرمجموعه آموزش‌دیده است">
            قسمتی
          </span>
        )}
        {node.question_count > 0 && (
          <span className="shrink-0 rounded-md bg-surface-2 px-1.5 py-0.5 text-[11px] font-semibold leading-4 text-muted">
            {faDigits(node.question_count)} سوال
          </span>
        )}
        <BlockTypeBadge type={node.block_type} label={node.block_type_fa} />

        <motion.button
          whileTap={{ scale: 0.95 }}
          transition={{ duration: D.fast }}
          onClick={() => void toggleTaught(!node.taught)}
          disabled={pending}
          className={[
            'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-colors disabled:opacity-50',
            node.taught ? 'border-success bg-success text-white' : 'border-border bg-surface text-transparent',
          ].join(' ')}
          aria-label={node.taught ? `«${node.title}» آموزش‌دیده نیست` : `«${node.title}» آموزش‌دیده است`}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 12.5 9.5 18 20 6.5" />
          </svg>
        </motion.button>
      </div>

      {toggleError && (
        <p className="mx-2 my-1 rounded-md bg-danger-soft px-3 py-1.5 text-body-sm text-danger" role="alert">
          {toggleError}
        </p>
      )}

      <AnimatePresence initial={false}>
        {hasChildren && open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: D.fast, ease: EASE_OUT }}
            className="overflow-hidden"
            role="group"
          >
            {node.children.map((child) => (
              <TopicRow key={child.id} node={child} depth={depth + 1} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
