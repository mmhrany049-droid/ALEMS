/**
 * Today Hub — doc 07.6 (مهم‌ترین صفحه).
 * Phase 0: greeting + Jalali date + live backend/system card + hub preview.
 * Sections ۲–۷ (check-in، ظرفیت، کارهای امروز، صف مرور، آزمون نزدیک،
 * پیشنهاد روز، sparkline) در فازهای ۱ تا ۵ می‌رسند — با cascade ورود (doc 07.4 #5).
 */
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card } from '../../components/Card'
import { EmptyState } from '../../components/EmptyState'
import { Icon } from '../../components/Icon'
import { Page } from '../../components/Page'
import { todayCascade, todayBlock } from '../../motion/variants'
import { todayJalali, formatJalaliLong, weekdayFa } from '../../lib/dates'
import { fetchHealth } from '../../lib/health'

const UPCOMING = [
  { icon: 'clock' as const, title: 'ظرفیت امروز', note: 'ظرفیت واقعی از time blocks و سابقه — فاز ۵' },
  { icon: 'check' as const, title: 'کارهای امروز', note: 'برنامه روز با checkbox انیمیشنی — فاز ۵' },
  { icon: 'review' as const, title: 'صف مرور ضروری', note: 'چرخه ۱-۳-۷-۱۴ — فاز ۴' },
  { icon: 'exam' as const, title: 'آزمون‌های نزدیک', note: 'Exam Center — فاز ۶' },
  { icon: 'sparkle' as const, title: 'پیشنهاد روز', note: 'Recommendation با «چرا؟» — فاز ۷' },
  { icon: 'progress' as const, title: 'خلاصه ۷ روز', note: 'sparkline پوشش/دقت/حجم — فاز ۶' },
]

export function TodayPage() {
  const t = todayJalali()
  const { data: health, isError } = useQuery({ queryKey: ['health'], queryFn: fetchHealth, staleTime: 60_000 })

  return (
    <Page>
      <motion.div variants={todayCascade} initial="initial" animate="animate" className="flex flex-col gap-4">
        {/* 1) سلام + تاریخ شمسی */}
        <motion.section variants={todayBlock} className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-display font-bold leading-tight">سلام 👋</h1>
            <p className="mt-2 text-body-lg text-muted">
              {weekdayFa(t)}، {formatJalaliLong(t)}
            </p>
          </div>
          {health && (
            <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-body-sm text-muted">
              <span className="h-2.5 w-2.5 rounded-full bg-success" />
              سیستم آماده است — نسخه {health.app_version}
            </div>
          )}
        </motion.section>

        {/* system card */}
        <motion.section variants={todayBlock}>
          <Card className="p-4 md:p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary-soft text-primary">
                <Icon name="sparkle" size={22} />
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-title-sm font-bold">فونداسیون ALEMS 2.0 فعال است</h2>
                <p className="mt-1 text-body-sm text-muted">
                  تقویم شمسی (هفته شنبه تا جمعه)، timezone Asia/Tehran، API روی پورت ۸۰۱۰ و پروکسی Vite.
                </p>
              </div>
            </div>
            {isError && (
              <p className="mt-3 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger">
                به backend وصل نشد؛ مطمئن شوید سرور روی ۸۰۱ در حال اجراست (scripts/run.sh).
              </p>
            )}
          </Card>
        </motion.section>

        {/* hub preview — cascade */}
        <motion.section variants={todayBlock} aria-label="بخش‌های Today Hub" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {UPCOMING.map((u) => (
            <motion.div key={u.title} variants={todayBlock}>
              <Card className="flex items-start gap-3 p-4 opacity-90">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-2 text-muted">
                  <Icon name={u.icon} size={18} />
                </div>
                <div>
                  <div className="text-body-sm font-semibold">{u.title}</div>
                  <div className="mt-0.5 text-body-sm text-muted">{u.note}</div>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.section>

        {/* empty state CTA (doc 07.8) */}
        <motion.section variants={todayBlock}>
          <EmptyState
            icon="book-open"
            text="حالا اولین کتابت را import کن تا مسیر کنکورت شکل بگیرد — بخش‌های بالا با داده‌ی تو زنده می‌شوند."
            action={
              <a
                href="/study"
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-body-sm font-semibold text-white shadow-soft transition-opacity hover:opacity-90"
              >
                <Icon name="book" size={17} />
                مرور بخش مطالعه
              </a>
            }
          />
        </motion.section>
      </motion.div>
    </Page>
  )
}
