/** BlockTypeBadge — badge نوع بلوک (doc 05/09: topic|mixed|chapter_exam|checkup|konkur|other). */
import type { BlockType } from '../lib/schemas'

const STYLES: Record<BlockType, string> = {
  topic: 'bg-primary-soft text-primary',
  mixed: 'bg-review-soft text-review',
  chapter_exam: 'bg-warning-soft text-warning',
  checkup: 'bg-success-soft text-success',
  konkur: 'bg-danger-soft text-danger',
  other: 'bg-surface-2 text-muted',
}

export function BlockTypeBadge({ type, label }: { type: BlockType; label?: string }) {
  return (
    <span
      className={[
        'inline-flex shrink-0 items-center rounded-md px-1.5 py-0.5',
        'text-[11px] font-semibold leading-4',
        STYLES[type] ?? STYLES.other,
      ].join(' ')}
    >
      {label ?? type}
    </span>
  )
}
