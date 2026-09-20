/**
 * Today Hub — «نقش امروز» (doc 07).
 * Phase 1: کارت «حالت امروز» (GET /students/me/state + CheckinCard) + چک‌لیست.
 * Phase 2+: برنامه‌ی روز، مرور‌های به‌روز، focus block — با API واقعی جایگزین می‌شوند.
 */
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import type { StateOut } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { CheckinCard } from '../../components/CheckinCard'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { faDigits, formatJalaliLong, todayJalali, weekdayFa } from '../../lib/dates'
import { D, EASE_OUT, listItem, staggerList } from '../../motion/variants'

export function TodayPage() {
  const qc = useQueryClient()
  const { data, isPending } = useQuery({ queryKey: ['state'], queryFn: () => api.get<StateOut>('/students/me/state') })
  const t = todayJalali()

  return (
    <Page
      title="امروز"
      subtitle={`${formatJalaliLong(t)} — ${weekdayFa(t)} · نقش امروزت را ببین، check-in بزن و شروع کن`}
    >
      <div className="grid gap-4 lg:grid-cols-2">
        {/* state */}
        {isPending ? (
          <Card className="flex items-center justify-center p-6">
            <div className="flex flex-col items-center gap-3 text-muted">
              <Spinner />
              <span className="text-body-sm">در حال بارگذاری حالت امروز…</span>
            </div>
          </Card>
        ) : (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: D.normal, ease: EASE_OUT }}>
            <CheckinCard state={data ?? null} onSaved={() => qc.invalidateQueries({ queryKey: ['state'] })} />
          </motion.div>
        )}

        {/* checklist */}
        <Card className="p-4 md:p-5">
          <h2 className="mb-4 text-title-sm font-bold">چک‌لیست امروز</h2>
          <motion.ul variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-1">
            {[
              'check-in صبح را ثبت کن',
              'فصل/موضوع اصلی امروز را مشخص کن',
              'حداقل یک مرور کوتاه از موضوعات قبل',
              'پایان روز: ساعت مطالعه را ثبت کن',
            ].map((item) => (
              <motion.li key={item} variants={listItem} className="flex items-center gap-2.5 rounded-md px-2 py-2.5">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-border" />
                <span className="text-body-sm">{item}</span>
              </motion.li>
            ))}
          </motion.ul>
          <div className="mt-4 rounded-md bg-surface-2 p-3">
            <p className="text-body-sm leading-6 text-muted">
              داده‌های check-in: <strong className="text-ink">{faDigits(data?.data_days ?? 0)}</strong> روز —
              هرچه بیشتر check-in بزنی، وضعیت‌سنجی دقیق‌تر می‌شود.
            </p>
          </div>
        </Card>
      </div>

      <Card className="mt-4 p-2">
        <EmptyState
          icon="book"
          text="برنامه‌ی روز هنوز ساخته نشده — بعد از وارد کردن کتاب (فاز ۲)، برنامه‌ی روز، مرور‌های به‌روز و focus block اینجا می‌آیند."
        />
      </Card>
    </Page>
  )
}
