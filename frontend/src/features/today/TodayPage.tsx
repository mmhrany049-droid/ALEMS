/**
 * Today Hub — doc 07.6 (مهم‌ترین صفحه) + phase-0 spec:
 * skeleton زیبا با داده mock (بدون داده واقعی):
 *   1) سلام  2) کارت ظرفیت  3) کارهای امروز (mock)  4) بلوک مرور  5) اتصال/health
 * ورود بلوک‌ها با cascade (doc 07.4 #5).
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card } from '../../components/Card'
import { Icon } from '../../components/Icon'
import { Page } from '../../components/Page'
import { todayCascade, todayBlock, staggerList, listItem, successPulse } from '../../motion/variants'
import { todayJalali, formatJalaliLong, weekdayFa, faDigits } from '../../lib/dates'
import { fetchHealth } from '../../lib/health'

/* ---------- mock data (phase 0 — بدون داده واقعی) ---------- */
const MOCK_TASKS = [
  { id: 't1', title: 'مطالعه: فصل ۲ فیزیک — الگوهای حرکتی', meta: 'مطالعه · ۴۵ دقیقه', done: true },
  { id: 't2', title: '۱۰ تست شیمی — فصل ۱ (الگوها و روندها)', meta: 'تست · ۲۰ دقیقه', done: false },
  { id: 't3', title: 'مرور ۵ مبحث بیولوژی از صف مرور', meta: 'مرور · ۳۰ دقیقه', done: false },
]

const MOCK_REVIEW = [
  { id: 'r1', title: 'شیمی · جدول دوره‌ای', note: '۲ غلط تکراری', critical: true },
  { id: 'r2', title: 'ریاضی · حد و پیوستگی', note: 'تیک مهم', critical: false },
]

export function TodayPage() {
  const t = todayJalali()
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: fetchHealth, staleTime: 60_000 })
  const [tasks, setTasks] = useState(MOCK_TASKS)
  const doneCount = tasks.filter((x) => x.done).length

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
          <span className="rounded-md border border-border bg-surface px-3 py-1.5 text-body-sm text-muted">
            داده‌های این صفحه نمونه است — بدون داده واقعی
          </span>
        </motion.section>

        <div className="grid gap-4 lg:grid-cols-3">
          {/* 2) کارت ظرفیت (mock) */}
          <motion.section variants={todayBlock} className="lg:col-span-1">
            <Card className="flex h-full flex-col gap-3 p-4 md:p-5">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary-soft text-primary">
                  <Icon name="clock" size={18} />
                </div>
                <h2 className="text-title-sm font-bold">ظرفیت امروز</h2>
              </div>
              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-display font-bold text-primary">{faDigits('180')}</span>
                  <span className="text-body-sm text-muted">دقیقه مطالعه تخمینی</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-valuenow={60} aria-valuemin={0} aria-valuemax={100}>
                  <motion.div
                    className="h-full origin-right rounded-full bg-primary"
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 0.6 }}
                    transition={{ duration: 0.4, ease: [0.45, 0, 0.55, 1] }}
                  />
                </div>
                <p className="mt-2 text-body-sm text-muted">{faDigits('60')}٪ برنامه امروز تخصیص یافته</p>
              </div>
            </Card>
          </motion.section>

          {/* 3) کارهای امروز (mock) */}
          <motion.section variants={todayBlock} className="lg:col-span-2">
            <Card className="flex h-full flex-col p-4 md:p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-title-sm font-bold">کارهای امروز</h2>
                <span className="text-body-sm text-muted">
                  {faDigits(doneCount)} از {faDigits(tasks.length)} انجام شد
                </span>
              </div>
              <motion.ul variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-2">
                {tasks.map((task) => (
                  <motion.li key={task.id} variants={listItem}>
                    <button
                      onClick={() =>
                        setTasks((prev) => prev.map((x) => (x.id === task.id ? { ...x, done: !x.done } : x)))
                      }
                      className={[
                        'flex w-full items-center gap-3 rounded-md border px-3 py-2.5 text-right transition-colors',
                        task.done
                          ? 'border-success/30 bg-success-soft'
                          : 'border-border bg-surface hover:bg-surface-2',
                      ].join(' ')}
                      aria-pressed={task.done}
                    >
                      <span
                        className={[
                          'flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2',
                          task.done ? 'border-success bg-success text-white' : 'border-border',
                        ].join(' ')}
                      >
                        {task.done && (
                          <motion.span variants={successPulse} initial="initial" animate="animate">
                            <Icon name="check" size={13} />
                          </motion.span>
                        )}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className={['block text-body-sm font-semibold', task.done ? 'line-through opacity-70' : ''].join(' ')}>
                          {task.title}
                        </span>
                        <span className="mt-0.5 block text-body-sm text-muted">{task.meta}</span>
                      </span>
                    </button>
                  </motion.li>
                ))}
              </motion.ul>
            </Card>
          </motion.section>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {/* 4) بلوک مرور (mock) */}
          <motion.section variants={todayBlock}>
            <Card className="flex h-full flex-col p-4 md:p-5">
              <div className="mb-3 flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-review-soft text-review">
                  <Icon name="review" size={18} />
                </div>
                <h2 className="text-title-sm font-bold">مرور ضروری</h2>
                <span className="mr-auto rounded-md bg-review-soft px-2 py-0.5 text-body-sm text-review">
                  {faDigits(MOCK_REVIEW.length)} مورد
                </span>
              </div>
              <motion.ul variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-2">
                {MOCK_REVIEW.map((r) => (
                  <motion.li key={r.id} variants={listItem}>
                    <div
                      className={[
                        'flex items-center justify-between gap-3 rounded-md border px-3 py-2.5',
                        r.critical ? 'border-warning/40 bg-warning-soft' : 'border-border bg-surface',
                      ].join(' ')}
                    >
                      <div className="min-w-0">
                        <div className="truncate text-body-sm font-semibold">{r.title}</div>
                        <div className={['text-body-sm', r.critical ? 'text-warning' : 'text-muted'].join(' ')}>
                          {r.note}
                        </div>
                      </div>
                      {r.critical && (
                        <span className="shrink-0 rounded-md bg-warning px-2 py-0.5 text-body-sm font-bold text-white">
                          بحرانی
                        </span>
                      )}
                    </div>
                  </motion.li>
                ))}
              </motion.ul>
            </Card>
          </motion.section>

          {/* 5) اتصال به backend — GET /health (اثبات اتصال از UI) */}
          <motion.section variants={todayBlock}>
            <Card className="flex h-full flex-col gap-3 p-4 md:p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-title-sm font-bold">وضعیت سامانه</h2>
                <span
                  className={[
                    'flex items-center gap-2 rounded-md px-2.5 py-1 text-body-sm',
                    health ? 'bg-success-soft text-success' : 'bg-danger-soft text-danger',
                  ].join(' ')}
                >
                  <span className={['h-2 w-2 rounded-full', health ? 'bg-success' : 'bg-danger'].join(' ')} />
                  {health ? 'متصل' : 'آفلاین'}
                </span>
              </div>
              {health ? (
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-body-sm">
                  <Row k="backend" v={`${health.app} v${faDigits(health.version)}`} />
                  <Row k="schema" v={faDigits(health.schema_version)} />
                  <Row k="پایگاه داده" v={health.db.type} />
                  <Row k="امروز (شمسی)" v={health.today_jalali} />
                  <Row k="هفته" v="شنبه تا جمعه" />
                  <Row k="timezone" v={health.timezone} />
                </dl>
              ) : (
                <p className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger">
                  به backend وصل نشد؛ مطمئن شوید سرور روی ۱۲۷.۰.۰.۱:۸۰۰ اجراست.
                </p>
              )}
            </Card>
          </motion.section>
        </div>
      </motion.div>
    </Page>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between gap-2 border-b border-border pb-1.5">
      <dt className="text-muted">{k}</dt>
      <dd className="font-semibold">{v}</dd>
    </div>
  )
}
