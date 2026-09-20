/** اشتراکات فاز ۳ — برچسب‌های فارسی، فرمت تاریخ/مدت، انتخاب کتاب و موضوع. */
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type { AttemptResult, AttemptStatus, BookResource, SessionMode, TreeNode } from '../../lib/schemas'
import { formatJalali, todayJalali, faDigits } from '../../lib/dates'

export const MODE_LABELS_FA: Record<SessionMode, string> = {
  timed: 'زمان‌دار',
  untimed: 'بدون زمان',
  past: 'نتایج قدیمی',
}

export const PARITY_LABELS_FA = { any: 'همه', odd: 'فرد', even: 'زوج' } as const

export const RESULT_LABELS_FA: Record<AttemptResult, string> = {
  correct: 'درست',
  wrong: 'غلط',
  blank: 'نزده',
  unknown: 'نامشخص',
}

export const STATUS_LABELS_FA: Record<AttemptStatus, string> = {
  answered: 'پاسخ داده',
  unanswered: 'نزده',
  not_entered: 'وارد نشده',
}

export const ERROR_TYPES_FA: { value: string; label: string }[] = [
  { value: 'careless', label: 'بی‌دقتی' },
  { value: 'concept', label: 'اشکال مفهومی' },
  { value: 'method', label: 'روش حل' },
  { value: 'memory', label: 'فراموشی' },
  { value: 'other', label: 'سایر' },
]

/** ISO → «۱۴۰۵/۰۶/۲۹» */
export function faDate(iso: string | null): string {
  if (!iso) return '—'
  return formatJalali(todayJalali(new Date(iso)))
}

/** seconds → «۷:۳۰» (m:ss) یا «۱:۰۲:۰۳» */
export function fmtClock(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const mm = String(m).padStart(2, '0')
  const ss = String(sec).padStart(2, '0')
  return faDigits(h > 0 ? `${h}:${mm}:${ss}` : `${m}:${ss}`)
}

export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '—'
  if (seconds < 60) return `${faDigits(seconds)} ثانیه`
  const m = Math.round(seconds / 60)
  return `${faDigits(m)} دقیقه`
}

export function fmtPercent(p: number | null): string {
  if (p == null) return '—'
  // درصد منفی نمایش داده می‌شود (doc 08 §8.1: show_negative=true)
  const body = faDigits(String(Math.abs(p)).replace('.', '٫'))
  return `${p < 0 ? '−' : ''}${body}٪`
}

export function useBooks() {
  return useQuery({
    queryKey: ['resources'],
    queryFn: () => api.get<{ items: BookResource[] }>('/resources'),
  })
}

export function useTree(bookId: string | null) {
  return useQuery({
    queryKey: ['resource-tree', bookId],
    enabled: !!bookId,
    queryFn: () => api.get<{ resource: BookResource; tree: TreeNode[] }>(`/resources/${bookId}/tree`),
  })
}

export interface FlatTopic {
  node: TreeNode
  depth: number
}

/** درخت → فهرست تخت با عمق (برای انتخاب موضوع/نمایش). */
export function flattenTree(tree: TreeNode[], depth = 0, out: FlatTopic[] = []): FlatTopic[] {
  for (const n of tree) {
    out.push({ node: n, depth })
    flattenTree(n.children, depth + 1, out)
  }
  return out
}

export const RESULT_CHIP: Record<AttemptResult, string> = {
  correct: 'bg-success-soft text-success',
  wrong: 'bg-danger-soft text-danger',
  blank: 'bg-warning-soft text-warning',
  unknown: 'bg-surface-2 text-muted',
}

export function ResultChip({ result }: { result: AttemptResult | null }) {
  if (!result) return <span className="text-body-sm text-muted">—</span>
  return (
    <span className={['inline-flex shrink-0 items-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold leading-4', RESULT_CHIP[result]].join(' ')}>
      {RESULT_LABELS_FA[result]}
    </span>
  )
}

export function ModeChip({ mode }: { mode: SessionMode }) {
  const cls = mode === 'past' ? 'bg-review-soft text-review' : mode === 'timed' ? 'bg-warning-soft text-warning' : 'bg-surface-2 text-muted'
  return (
    <span className={['inline-flex shrink-0 items-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold leading-4', cls].join(' ')}>
      {MODE_LABELS_FA[mode]}
    </span>
  )
}
