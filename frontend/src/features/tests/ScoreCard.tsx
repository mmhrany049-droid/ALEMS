/**
 * ScoreCard — نمایش نمره جلسه (doc 08 §8.1).
 * درصد کنکوری (با k=0.33) + درصد بدون منفی + شمارش‌های جدا
 * (درست/غلط/نزده/واردنشده — Coverage≠Accuracy≠Volume، هرگز یک عدد جایگزین سه‌تا نمی‌شود).
 * درصد منفی همان‌طور که هست نمایش داده می‌شود (show_negative=true).
 */
import { motion } from 'framer-motion'
import type { TestSessionOut, TopicAggregate } from '../../lib/schemas'
import { Card } from '../../components/Card'
import { faDigits } from '../../lib/dates'
import { fmtDuration, fmtPercent } from './shared'
import { successPulse, D, EASE_OUT } from '../../motion/variants'

function CountCell({ label, value, cls }: { label: string; value: number; cls: string }) {
  return (
    <div className="flex flex-col items-center gap-0.5 rounded-md bg-surface-2 px-2 py-2">
      <span className={['text-title-sm font-bold', cls].join(' ')}>{faDigits(value)}</span>
      <span className="text-body-sm text-muted">{label}</span>
    </div>
  )
}

export function ScoreCard({ session, topics }: { session: TestSessionOut; topics?: TopicAggregate[] }) {
  const pk = session.percent_konkur
  const negative = pk != null && pk < 0
  return (
    <Card className="flex flex-col gap-4 p-4 md:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-title-sm font-bold">{session.label || session.resource_title || 'جلسه'}</h3>
          <p className="mt-0.5 text-body-sm text-muted">
            {faDigits(session.total_count)} سوال · k={session.penalty_k != null ? faDigits(String(session.penalty_k).replace('.', '٫')) : '۰٫۳۳'}
            {session.actual_duration != null && ` · مدت: ${fmtDuration(session.actual_duration)}`}
          </p>
        </div>
        <motion.div
          variants={successPulse}
          initial="initial"
          animate="animate"
          transition={{ duration: D.slow, ease: EASE_OUT }}
          className="flex flex-col items-center"
        >
          <span className={['text-display-lg font-bold leading-none', negative ? 'text-danger' : 'text-primary'].join(' ')}>
            {fmtPercent(pk)}
          </span>
          <span className="mt-1 text-body-sm text-muted">درصد کنکوری</span>
        </motion.div>
      </div>

      <div className="grid grid-cols-4 gap-2">
        <CountCell label="درست" value={session.correct_count} cls="text-success" />
        <CountCell label="غلط" value={session.wrong_count} cls="text-danger" />
        <CountCell label="نزده" value={session.unanswered_count} cls="text-warning" />
        <CountCell label="واردنشده" value={session.not_entered_count} cls="text-muted" />
      </div>

      <div className="flex items-center justify-between rounded-md bg-surface-2 px-3 py-2 text-body-sm">
        <span className="text-muted">درصد بدون منفی (C/T)</span>
        <span className="font-bold">{fmtPercent(session.percent_no_penalty)}</span>
      </div>

      {topics && topics.length > 0 && (
        <div>
          <h4 className="mb-2 text-body-sm font-bold text-muted">زمان و نتیجه به تفکیک موضوع</h4>
          <div className="flex flex-col gap-1">
            {topics.map((t, i) => (
              <div key={`${t.topic_id ?? i}`} className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-body-sm hover:bg-surface-2">
                <span className="min-w-0 flex-1 truncate">{t.topic_title || '—'}</span>
                <span className="shrink-0 text-success">{faDigits(t.correct)}✓</span>
                <span className="shrink-0 text-danger">{faDigits(t.wrong)}✗</span>
                <span className="shrink-0 text-muted">{fmtDuration(t.duration_seconds)}</span>
                <span className="hidden shrink-0 text-muted sm:inline">میانگین {faDigits(String(t.avg_seconds).replace('.', '٫'))}s</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
