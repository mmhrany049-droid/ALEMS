/**
 * Progress — تحلیل و گزارش (doc 12، فاز ۶).
 * - V2-A01 (قید ۲): Coverage / Accuracy / Volume همیشه سه بلوک جدا — هرگز یک عدد قاطی.
 * - نمودارها با Recharts (doc 03 §3.2 stack اجباری).
 * - گزارش هفتگی + هدف کنکور (فقط کیفی — doc 12.4، بدون ادعای رتبه).
 * - Export: JSON کامل (V2-A02) · Excel RTL · PDF فارسی (doc 12.5).
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, ApiError, apiBlob, saveBlob } from '../../lib/api'
import type {
  BySubjectItem,
  ByTopicItem,
  DifficultyItem,
  MistakesOut,
  OverviewOut,
  PdfReportKind,
  WeeklyReport,
} from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Icon } from '../../components/Icon'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { listItem, progressFill, staggerList } from '../../motion/variants'
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const pct = (v: number | null, digits = 0) =>
  v === null || v === undefined ? '—' : `${faDigits((v * 100).toFixed(digits))}٪`
const numFa = (v: number | null) => (v === null || v === undefined ? '—' : faDigits(v))
const dayTick = (j: string) => faDigits(j.slice(-2))

const PDF_KINDS: { id: PdfReportKind; fa: string }[] = [
  { id: 'daily', fa: 'روزانه' },
  { id: 'weekly', fa: 'هفتگی' },
  { id: 'monthly', fa: 'ماهانه' },
  { id: 'summary', fa: 'خلاصه' },
]

export function ProgressPage() {
  const [days, setDays] = useState(30)
  const [topicOrder, setTopicOrder] = useState<'volume' | 'accuracy' | 'readiness'>('volume')
  const [pdfKind, setPdfKind] = useState<PdfReportKind>('weekly')
  const [dlMsg, setDlMsg] = useState<string | null>(null)

  const overviewQ = useQuery({
    queryKey: ['overview', days],
    queryFn: () => api.get<OverviewOut>(`/analytics/overview?days=${days}`),
  })
  const weeklyQ = useQuery({ queryKey: ['weekly-report'], queryFn: () => api.get<WeeklyReport>('/reports/weekly') })
  const subjectQ = useQuery({ queryKey: ['by-subject'], queryFn: () => api.get<{ items: BySubjectItem[] }>('/analytics/by-subject') })
  const topicQ = useQuery({
    queryKey: ['by-topic', topicOrder],
    queryFn: () => api.get<{ items: ByTopicItem[]; order: string; total: number }>(`/analytics/by-topic?order=${topicOrder}&limit=12`),
  })
  const diffQ = useQuery({ queryKey: ['difficulty'], queryFn: () => api.get<{ items: DifficultyItem[] }>('/analytics/difficulty') })
  const mistakesQ = useQuery({ queryKey: ['mistakes'], queryFn: () => api.get<MistakesOut>('/analytics/mistakes') })

  const downloadM = useMutation({
    mutationFn: async (which: 'json' | 'excel' | 'pdf') => {
      if (which === 'json') {
        // JSON کامل (V2-A02) — books + attempts همیشه داخلش هست
        const data = await api.get<Record<string, unknown>>('/export/json')
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        saveBlob(blob, 'alems-export.json')
        return 'خروجی JSON کامل گرفته شد (شامل کتاب‌ها و تلاش‌ها).'
      }
      const r = await apiBlob(which === 'excel' ? '/export/excel' : `/export/pdf?report=${pdfKind}`)
      saveBlob(r.blob, r.filename)
      return which === 'excel' ? 'فایل Excel (RTL) دانلود شد.' : `گزارش PDF «${PDF_KINDS.find((k) => k.id === pdfKind)?.fa}» دانلود شد.`
    },
    onSuccess: (m) => setDlMsg(m),
    onError: (e) => setDlMsg(e instanceof ApiError ? e.message : 'دانلود ناموفق بود.'),
  })

  if (overviewQ.isLoading) {
    return (
      <Page title="پیشرفت" subtitle="پوشش، دقت و حجم — همیشه جدا از هم">
        <div className="flex justify-center py-16"><Spinner /></div>
      </Page>
    )
  }
  if (overviewQ.isError || !overviewQ.data) {
    const msg = overviewQ.error instanceof ApiError ? overviewQ.error.message : 'خطا در دریافت تحلیل.'
    return (
      <Page title="پیشرفت">
        <EmptyState icon="progress" text={msg} action={<Button variant="soft" onClick={() => overviewQ.refetch()}>تلاش دوباره</Button>} />
      </Page>
    )
  }
  const d = overviewQ.data

  return (
    <Page title="پیشرفت" subtitle="پوشش، دقت و حجم — همیشه جدا از هم">
      <motion.div variants={staggerList} initial="initial" animate="animate" className="space-y-5">
        {/* پنجره زمانی */}
        <motion.div variants={listItem} className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-body-sm text-muted">
            پنجره تحلیل: {faDigits(d.window.start_jalali)} تا {faDigits(d.window.end_jalali)}
          </p>
          <div className="flex gap-1.5">
            {[7, 30, 90].map((n) => (
              <button
                key={n} type="button" onClick={() => setDays(n)}
                className={`rounded-lg px-3 py-1 text-body-sm font-semibold transition-colors ${
                  days === n ? 'bg-primary text-white' : 'bg-surface-2 text-muted hover:text-ink'
                }`}
              >
                {faDigits(n)} روز
              </button>
            ))}
          </div>
        </motion.div>

        {/* --- V2-A01: سه بلوک کاملاً جدا --- */}
        <motion.div variants={listItem} className="grid gap-4 md:grid-cols-3">
          <CoverageCard cov={d.coverage} />
          <AccuracyCard acc={d.accuracy} days={days} />
          <VolumeCard vol={d.volume} days={days} />
        </motion.div>

        {/* --- نمودار روزانه (Recharts) --- */}
        <motion.div variants={listItem}>
          <Card className="p-4 md:p-5">
            <h2 className="text-title-sm font-bold">روند {faDigits(days)} روز اخیر</h2>
            <p className="mb-3 text-[11px] text-muted">ستون‌ها: درست/غلط هر روز · خط: دقیقه مطالعه (محور چپ)</p>
            <div dir="ltr" style={{ height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={d.daily} margin={{ top: 6, right: 6, left: -18, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="date_jalali" tickFormatter={dayTick} tick={{ fontSize: 10 }} interval="preserveStartEnd" minTickGap={14} />
                  <YAxis yAxisId="q" tick={{ fontSize: 10 }} allowDecimals={false} />
                  <YAxis yAxisId="m" orientation="right" tick={{ fontSize: 10 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ direction: 'rtl', fontFamily: 'Vazirmatn, sans-serif', fontSize: 12, borderRadius: 12 }}
                    labelFormatter={(l) => faDigits(String(l))}
                    formatter={(value: number | string, name: string) => [faDigits(Number(value)), name]}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, direction: 'rtl' }} />
                  <Bar yAxisId="q" dataKey="correct" name="درست" stackId="a" fill="var(--color-success)" radius={[0, 0, 0, 0]} />
                  <Bar yAxisId="q" dataKey="wrong" name="غلط" stackId="a" fill="var(--color-danger)" radius={[3, 3, 0, 0]} />
                  <Line yAxisId="m" type="monotone" dataKey="study_minutes" name="دقیقه مطالعه" stroke="var(--color-primary)" strokeWidth={2} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </motion.div>

        {/* --- هدف کنکور (فقط کیفی — doc 12.4) --- */}
        <motion.div variants={listItem}>
          <Card className="border-primary/30 bg-primary-soft/30 p-4 md:p-5">
            <div className="flex items-center gap-2">
              <Icon name="target" size={18} />
              <h2 className="text-title-sm font-bold">هدف کنکور — نگاه کیفی</h2>
            </div>
            {d.konkurs_target.has_target ? (
              <>
                <p className="mt-2 text-body font-semibold">{d.konkurs_target.message_fa}</p>
                {d.konkurs_target.level_fa && (
                  <p className="mt-1 text-body-sm text-muted">
                    سطح فعلی: {d.konkurs_target.level_fa}
                    {d.konkurs_target.based_on.answered_accuracy !== null &&
                      ` · دقت در پاسخ‌ها ${pct(d.konkurs_target.based_on.answered_accuracy)}`}
                    {d.konkurs_target.based_on.topics_ratio !== null &&
                      ` · پوشش مباحث ${pct(d.konkurs_target.based_on.topics_ratio)}`}
                  </p>
                )}
              </>
            ) : (
              <p className="mt-2 text-body-sm text-muted">{d.konkurs_target.message_fa}</p>
            )}
            <p className="mt-2 text-[10px] leading-4 text-muted">
              این بخش فقط کیفی است و هیچ رتبه یا تراز دقیقی ادعا نمی‌کند (doc 12.4).
            </p>
          </Card>
        </motion.div>

        {/* --- کارت هفتگی (doc 12.5 report weekly) --- */}
        <motion.div variants={listItem}>
          <WeeklyCard w={weeklyQ.data} loading={weeklyQ.isLoading} />
        </motion.div>

        {/* --- برش‌ها --- */}
        <motion.div variants={listItem} className="grid gap-4 lg:grid-cols-2">
          <SubjectChart items={subjectQ.data?.items ?? []} loading={subjectQ.isLoading} />
          <DifficultyChart items={diffQ.data?.items ?? []} loading={diffQ.isLoading} />
        </motion.div>

        <motion.div variants={listItem}>
          <Card className="p-4 md:p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-title-sm font-bold">مباحث — سه متریک جدا در هر ردیف</h2>
              <div className="flex gap-1.5">
                {([['volume', 'حجم'], ['accuracy', 'دقت'], ['readiness', 'آمادگی']] as const).map(([id, fa]) => (
                  <button
                    key={id} type="button" onClick={() => setTopicOrder(id)}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold ${
                      topicOrder === id ? 'bg-primary text-white' : 'bg-surface-2 text-muted'
                    }`}
                  >
                    {fa}
                  </button>
                ))}
              </div>
            </div>
            {topicQ.isLoading ? (
              <div className="flex justify-center py-6"><Spinner /></div>
            ) : (topicQ.data?.items ?? []).length === 0 ? (
              <p className="py-4 text-body-sm text-muted">داده‌ای برای نمایش نیست.</p>
            ) : (
              <div className="mt-3 space-y-2">
                {(topicQ.data?.items ?? []).map((t) => (
                  <div key={t.topic_id} className="grid grid-cols-[1fr_auto] items-center gap-2 rounded-xl bg-surface-2 px-3 py-2 sm:grid-cols-[2fr_1fr_1fr_1fr]">
                    <div className="min-w-0">
                      <p className="truncate text-body-sm font-semibold">
                        {t.topic_title ?? '—'}
                        {t.weakness && <span className="mr-1.5 rounded bg-danger-soft px-1.5 py-0.5 text-[10px] text-danger">ضعیف</span>}
                      </p>
                      <p className="truncate text-[10px] text-muted">{t.book_title ?? ''}{t.chapter_title ? ` · ${t.chapter_title}` : ''}</p>
                    </div>
                    <MetricCell label="پوشش" value={pct(t.coverage.questions_ratio)} />
                    <MetricCell label="دقت" value={pct(t.accuracy.answered_accuracy)} />
                    <MetricCell label="آمادگی" value={pct(t.exam_readiness)} />
                  </div>
                ))}
              </div>
            )}
          </Card>
        </motion.div>

        {/* --- خطاها و نقاط ضعف --- */}
        <motion.div variants={listItem} className="grid gap-4 lg:grid-cols-2">
          <MistakesCard m={mistakesQ.data} loading={mistakesQ.isLoading} />
          <Card className="p-4 md:p-5">
            <h2 className="text-title-sm font-bold">نقاط ضعف (از وضعیت یادگیری)</h2>
            {d.weaknesses.length === 0 ? (
              <p className="mt-2 text-body-sm text-muted">نقطه ضعف ثبت‌شده‌ای نیست — آفرین!</p>
            ) : (
              <div className="mt-3 space-y-2">
                {d.weaknesses.map((w, i) => (
                  <div key={w.topic_id ?? i} className="flex items-center justify-between gap-2 rounded-xl bg-surface-2 px-3 py-2 text-body-sm">
                    <span className="truncate font-semibold">{w.topic_title ?? '—'}</span>
                    <span className="shrink-0 text-muted tabular-nums">
                      پوشش {pct(w.coverage)} · دقت {pct(w.accuracy)} · آمادگی {pct(w.exam_readiness)}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {/* time buckets */}
            {d.time_buckets.length > 0 && (
              <div className="mt-4">
                <h3 className="text-body-sm font-bold">دقت در بازه‌های روز</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {d.time_buckets.map((b) => (
                    <div key={b.bucket} className="rounded-xl bg-surface-2 px-3 py-2 text-center">
                      <p className="text-body-sm font-bold tabular-nums">{pct(b.answered_accuracy)}</p>
                      <p className="text-[10px] text-muted">{b.bucket} · {faDigits(b.attempts)} پاسخ</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </motion.div>

        {/* --- Export (doc 12.5) --- */}
        <motion.div variants={listItem}>
          <Card className="p-4 md:p-5">
            <h2 className="text-title-sm font-bold">خروجی گرفتن</h2>
            <p className="mt-1 text-body-sm text-muted">
              JSON کامل کاربر (شامل کتاب‌ها و تلاش‌ها) · Excel فارسی راست‌به‌چپ · PDF گزارش با فونت وزیرمتن.
            </p>
            <div className="mt-3 flex flex-wrap items-end gap-3">
              <Button variant="soft" onClick={() => downloadM.mutate('json')} disabled={downloadM.isPending}>
                دانلود JSON
              </Button>
              <Button variant="soft" onClick={() => downloadM.mutate('excel')} disabled={downloadM.isPending}>
                دانلود Excel
              </Button>
              <div className="flex items-end gap-2">
                <div>
                  <label className="mb-1 block text-[11px] text-muted">نوع گزارش PDF</label>
                  <select
                    value={pdfKind} onChange={(e) => setPdfKind(e.target.value as PdfReportKind)}
                    className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-body-sm outline-none focus:border-primary"
                  >
                    {PDF_KINDS.map((k) => <option key={k.id} value={k.id}>{k.fa}</option>)}
                  </select>
                </div>
                <Button onClick={() => downloadM.mutate('pdf')} disabled={downloadM.isPending}>
                  {downloadM.isPending ? 'در حال ساخت…' : 'دانلود PDF'}
                </Button>
              </div>
            </div>
            {dlMsg && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 rounded-lg bg-surface-2 px-3 py-2 text-body-sm">
                {dlMsg}
              </motion.p>
            )}
          </Card>
        </motion.div>
      </motion.div>
    </Page>
  )
}

// --- سه بلوک متریک (V2-A01) ------------------------------------------------------------------

function CoverageCard({ cov }: { cov: OverviewOut['coverage'] }) {
  return (
    <Card className="p-4 md:p-5">
      <div className="flex items-center gap-2">
        <Icon name="book-open" size={16} />
        <h2 className="text-title-sm font-bold">پوشش</h2>
        <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted">از ابتدا تا امروز</span>
      </div>
      <p className="mt-3 text-title font-bold tabular-nums">{pct(cov.topics_ratio)}</p>
      <p className="text-body-sm text-muted">
        {faDigits(cov.topics_attempted)} از {faDigits(cov.topics_total)} مبحث تدریس‌شده
      </p>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-2">
        <motion.div className="h-full rounded-full bg-primary" style={{ width: `${(cov.topics_ratio ?? 0) * 100}%` }} variants={progressFill} initial="initial" animate="animate" />
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <p className="text-body-sm font-semibold tabular-nums">{pct(cov.questions_ratio)}</p>
        <p className="text-[11px] text-muted">
          {faDigits(cov.questions_attempted)} از {faDigits(cov.questions_total)} سوال
        </p>
      </div>
      {cov.by_resource.length > 0 && (
        <div className="mt-3 space-y-1.5 border-t border-border pt-2">
          {cov.by_resource.slice(0, 4).map((r) => (
            <div key={r.resource_id} className="flex items-center justify-between text-[11px]">
              <span className="truncate">{r.title}</span>
              <span className="text-muted tabular-nums">{faDigits(r.topics_attempted)}/{faDigits(r.topics_total)}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function AccuracyCard({ acc, days }: { acc: OverviewOut['accuracy']; days: number }) {
  return (
    <Card className="p-4 md:p-5">
      <div className="flex items-center gap-2">
        <Icon name="check" size={16} />
        <h2 className="text-title-sm font-bold">دقت</h2>
        <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted">{faDigits(days)} روز اخیر</span>
      </div>
      <p className="mt-3 text-title font-bold tabular-nums">{pct(acc.answered_accuracy)}</p>
      <p className="text-body-sm text-muted">دقت در پاسخ‌های داده‌شده</p>
      <div className="mt-2 flex gap-1.5 text-[11px]">
        <span className="rounded-md bg-success-soft px-2 py-0.5 text-success tabular-nums">{faDigits(acc.correct)} درست</span>
        <span className="rounded-md bg-danger-soft px-2 py-0.5 text-danger tabular-nums">{faDigits(acc.wrong)} غلط</span>
        <span className="rounded-md bg-warning-soft px-2 py-0.5 text-warning tabular-nums">{faDigits(acc.unanswered)} بی‌پاسخ</span>
      </div>
      {/* دو درصد همیشه جدا — §8.1 */}
      <div className="mt-3 space-y-1.5 border-t border-border pt-2">
        <div className="flex items-center justify-between text-body-sm">
          <span className="text-muted">درصد کنکوری (با جریمه k={numFa(acc.penalty_k)})</span>
          <span className={`font-bold tabular-nums ${(acc.percent_konkur ?? 0) < 0 ? 'text-danger' : 'text-primary'}`}>{pct1(acc.percent_konkur)}</span>
        </div>
        <div className="flex items-center justify-between text-body-sm">
          <span className="text-muted">بدون جریمه</span>
          <span className="font-bold tabular-nums">{pct1(acc.percent_no_penalty)}</span>
        </div>
      </div>
    </Card>
  )
}

const pct1 = (v: number | null) => (v === null || v === undefined ? '—' : `${faDigits(Math.round(v * 10) / 10)}٪`)

function VolumeCard({ vol, days }: { vol: OverviewOut['volume']; days: number }) {
  return (
    <Card className="p-4 md:p-5">
      <div className="flex items-center gap-2">
        <Icon name="clock" size={16} />
        <h2 className="text-title-sm font-bold">حجم</h2>
        <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted">{faDigits(days)} روز اخیر</span>
      </div>
      <p className="mt-3 text-title font-bold tabular-nums">{faDigits(vol.attempts)}</p>
      <p className="text-body-sm text-muted">پاسخ ثبت‌شده</p>
      <div className="mt-3 grid grid-cols-2 gap-2 border-t border-border pt-3 text-[11px]">
        <VolCell label="جلسه تست" value={numFa(vol.sessions)} />
        <VolCell label="دقیقه مطالعه" value={numFa(vol.study_minutes)} />
        <VolCell label="روز فعال" value={numFa(vol.active_days)} />
        <VolCell label="مرور انجام‌شده" value={numFa(vol.reviews_done)} />
        <VolCell label="دقیقه آزمون" value={numFa(vol.test_duration_minutes)} />
        <VolCell label="میانگین پاسخ/روز فعال" value={numFa(vol.avg_attempts_per_active_day)} />
      </div>
    </Card>
  )
}

function VolCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface-2 px-2 py-1.5">
      <span className="font-bold tabular-nums">{value}</span>
      <span className="mr-1 text-muted">{label}</span>
    </div>
  )
}

function MetricCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center sm:text-right">
      <p className="text-body-sm font-bold tabular-nums">{value}</p>
      <p className="text-[10px] text-muted">{label}</p>
    </div>
  )
}

// --- کارت هفتگی -------------------------------------------------------------------------------

function WeeklyCard({ w, loading }: { w: WeeklyReport | undefined; loading: boolean }) {
  if (loading) return <Card className="flex justify-center p-6"><Spinner /></Card>
  if (!w) return null
  const pw = w.previous_week
  const delta = (v: number) => (
    <span className={v > 0 ? 'text-success' : v < 0 ? 'text-danger' : 'text-muted'}>
      {v > 0 ? '▲' : v < 0 ? '▼' : '＝'} {faDigits(Math.abs(v))}
    </span>
  )
  return (
    <Card className="p-4 md:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-title-sm font-bold">گزارش هفته</h2>
        <p className="text-body-sm text-muted tabular-nums">
          {faDigits(w.week_start_jalali)} تا {faDigits(w.week_end_jalali)}
        </p>
      </div>
      {/* نوار ۷ روز */}
      <div className="mt-3 grid grid-cols-7 gap-1.5">
        {w.days.map((day) => (
          <div
            key={day.date}
            className={`rounded-lg px-1 py-2 text-center ${day.is_today ? 'border border-primary bg-primary-soft' : 'bg-surface-2'}`}
            title={`${day.date_jalali} — ${day.attempts} پاسخ، ${day.study_minutes} دقیقه`}
          >
            <p className="text-[10px] text-muted">{day.weekday_fa.slice(0, 3)}</p>
            <p className="text-body-sm font-bold tabular-nums">{faDigits(day.attempts)}</p>
            <p className="text-[9px] text-muted tabular-nums">{faDigits(day.study_minutes)}د</p>
          </div>
        ))}
      </div>
      <div className="mt-3 grid gap-2 text-[11px] sm:grid-cols-3">
        <div className="rounded-lg bg-surface-2 px-3 py-2">
          <p className="text-muted">نسبت به هفته قبل</p>
          <p className="mt-0.5 font-semibold">پاسخ‌ها {delta(pw.attempts_delta)} · مطالعه {delta(pw.study_minutes_delta)}</p>
        </div>
        <div className="rounded-lg bg-surface-2 px-3 py-2">
          <p className="text-muted">ظرفیت هفته</p>
          <p className="mt-0.5 font-semibold tabular-nums">
            {faDigits(w.capacity.used_minutes)} از {faDigits(w.capacity.available_minutes)} دقیقه
            {w.capacity.usage_ratio !== null ? ` (${pct(w.capacity.usage_ratio)})` : ''}
          </p>
        </div>
        <div className="rounded-lg bg-surface-2 px-3 py-2">
          <p className="text-muted">دقت هفته (پاسخ‌ها)</p>
          <p className="mt-0.5 font-semibold tabular-nums">{pct(w.accuracy.answered_accuracy)} · کنکوری {pct1(w.accuracy.percent_konkur)}</p>
        </div>
      </div>
      {w.exams.length > 0 && (
        <div className="mt-3 border-t border-border pt-2">
          <p className="text-[11px] text-muted">آزمون‌های این هفته</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {w.exams.map((e) => (
              <span key={e.id} className="rounded-lg bg-surface-2 px-2.5 py-1 text-[11px]">
                {e.title} · {faDigits(e.scheduled_date_jalali ?? '—')}
                {e.percent_konkur !== null ? ` · کنکوری ${pct1(e.percent_konkur)}` : ''}
              </span>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

// --- نمودار برش‌ها -----------------------------------------------------------------------------

function SubjectChart({ items, loading }: { items: BySubjectItem[]; loading: boolean }) {
  const data = items.map((i) => ({
    name: i.title,
    attempts: i.volume.attempts,
    accuracy: i.accuracy.answered_accuracy === null ? 0 : Math.round(i.accuracy.answered_accuracy * 100),
  }))
  return (
    <Card className="p-4 md:p-5">
      <h2 className="text-title-sm font-bold">تفکیک کتاب‌ها</h2>
      <p className="mb-3 text-[11px] text-muted">ستون: تعداد پاسخ · خط: دقت ٪ (جدا از هم)</p>
      {loading || data.length === 0 ? (
        <p className="py-6 text-center text-body-sm text-muted">داده‌ای نیست.</p>
      ) : (
        <div dir="ltr" style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ direction: 'rtl', fontFamily: 'Vazirmatn, sans-serif', fontSize: 12, borderRadius: 12 }}
                formatter={(value: number | string, name: string) => [faDigits(Number(value)), name === 'accuracy' ? 'دقت ٪' : 'پاسخ']}
              />
              <Bar dataKey="attempts" name="attempts" fill="var(--color-primary)" radius={[0, 6, 6, 0]} barSize={14} />
              <Line dataKey="accuracy" name="accuracy" stroke="var(--color-warning)" strokeWidth={2} dot={{ r: 3 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}

function DifficultyChart({ items, loading }: { items: DifficultyItem[]; loading: boolean }) {
  const data = items.map((i) => ({
    name: i.difficulty_fa,
    attempts: i.volume.attempts,
    acc: i.accuracy.answered_accuracy === null ? null : Math.round(i.accuracy.answered_accuracy * 100),
  }))
  return (
    <Card className="p-4 md:p-5">
      <h2 className="text-title-sm font-bold">تفکیک سختی</h2>
      <p className="mb-3 text-[11px] text-muted">تعداد پاسخ در هر سطح سختی · رنگ: دقت</p>
      {loading || data.length === 0 ? (
        <p className="py-6 text-center text-body-sm text-muted">داده‌ای نیست.</p>
      ) : (
        <div dir="ltr" style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ direction: 'rtl', fontFamily: 'Vazirmatn, sans-serif', fontSize: 12, borderRadius: 12 }}
                formatter={(value: number | string, name: string) => [faDigits(Number(value)), name === 'acc' ? 'دقت ٪' : 'پاسخ']}
              />
              <Bar dataKey="attempts" name="attempts" radius={[6, 6, 0, 0]} barSize={30}>
                {data.map((row, i) => (
                  <Cell
                    key={i}
                    fill={row.acc === null ? 'var(--color-text-muted)' : row.acc >= 60 ? 'var(--color-success)' : row.acc >= 35 ? 'var(--color-warning)' : 'var(--color-danger)'}
                  />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}

function MistakesCard({ m, loading }: { m: MistakesOut | undefined; loading: boolean }) {
  if (loading) return <Card className="flex justify-center p-6"><Spinner /></Card>
  if (!m) return null
  return (
    <Card className="p-4 md:p-5">
      <h2 className="text-title-sm font-bold">تحلیل خطاها</h2>
      {m.notes_total === 0 && m.top_wrong_topics.length === 0 ? (
        <p className="mt-2 text-body-sm text-muted">خطایی ثبت نشده.</p>
      ) : (
        <div className="mt-3 space-y-3 text-body-sm">
          {m.top_wrong_topics.length > 0 && (
            <div>
              <p className="text-[11px] text-muted">پرتکرارترین مباحث غلط</p>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {m.top_wrong_topics.map((t, i) => (
                  <span key={i} className="rounded-lg bg-danger-soft px-2 py-1 text-[11px] text-danger">
                    {t.topic_title ?? '—'} · {faDigits(t.wrong_count)} غلط
                  </span>
                ))}
              </div>
            </div>
          )}
          {m.by_error_type.length > 0 && (
            <div>
              <p className="text-[11px] text-muted">برچسب خطاها</p>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {m.by_error_type.map((t, i) => (
                  <span key={i} className="rounded-lg bg-surface-2 px-2 py-1 text-[11px]">
                    {t.error_type_fa} · {faDigits(t.count)}
                  </span>
                ))}
              </div>
            </div>
          )}
          {m.repeated_wrong_questions.length > 0 && (
            <div>
              <p className="text-[11px] text-muted">سوالات با غلط تکراری (≥۲)</p>
              <div className="mt-1 space-y-1">
                {m.repeated_wrong_questions.slice(0, 5).map((q, i) => (
                  <div key={i} className={`rounded-lg px-2.5 py-1.5 text-[11px] ${q.critical ? 'bg-danger-soft text-danger' : 'bg-surface-2'}`}>
                    {q.book_title ?? ''} · {q.topic_title ?? ''} · سوال {numFa(q.question_number)} — {faDigits(q.wrong_count)} بار غلط
                  </div>
                ))}
              </div>
            </div>
          )}
          {m.notes_unlabeled > 0 && (
            <p className="rounded-lg bg-warning-soft px-3 py-2 text-[11px] text-warning">
              {faDigits(m.notes_unlabeled)} یادداشت خطا بدون برچسب است — در «تست‌ها → دفترچه خطا» برچسب بزن تا تحلیل دقیق‌تر شود.
            </p>
          )}
        </div>
      )}
    </Card>
  )
}
