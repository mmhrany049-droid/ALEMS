/**
 * Plan — برنامه هفته با ظرفیت واقعی و override دستی (doc 11، doc 08 §8.6-8.7).
 * generate-week با نمایش ۱۲ مرحله pipeline (plannerStep — doc 07.4 #8)،
 * lock/split/merge/move/status/delete (doc 11.4)، time-blocks و school override (V2-P02)،
 * recovery با پخش در هفته (V2-P04).
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type {
  CapacityOut, GenerateWeekOut, PlanDayOut, PlanTaskIn, PlanTaskOut,
  RecoveryOut, TimeBlockIn, TimeBlockOut, TimeBlocksOut, TodayOut,
} from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { ConfirmButton } from '../../components/ConfirmButton'
import { EmptyState } from '../../components/EmptyState'
import { Spinner } from '../../components/Spinner'
import { Icon } from '../../components/Icon'
import { faDigits } from '../../lib/dates'
import { fadeInUp, listItem, plannerStep, staggerList } from '../../motion/variants'

/** ۱۲ مرحله ثابت pipeline — doc 11.3، همان ترتیب backend. */
const PIPELINE_FA: [string, string][] = [
  ['load_context', 'بارگذاری زمینه هفته'],
  ['exams', 'آزمون‌های پیش‌رو'],
  ['goals', 'اهداف فعال'],
  ['taught_filter', 'فیلتر مباحث تدریس‌شده'],
  ['learning_states', 'وضعیت‌های یادگیری'],
  ['review_demand', 'تقاضای مرور'],
  ['priority_items', 'محاسبه اولویت‌ها'],
  ['capacity_per_day', 'ظرفیت روز به روز'],
  ['allocate_tasks', 'تخصیص کارها'],
  ['overload_check', 'کنترل بار اضافی'],
  ['explain', 'تولید دلیل‌ها'],
  ['save_suggested', 'ذخیره به‌عنوان پیشنهاد (نه قطعی)'],
]

const KIND_BADGE: Record<string, string> = {
  study: 'bg-primary-soft text-primary',
  test: 'bg-warning-soft text-warning',
  review: 'bg-review-soft text-review',
  goal: 'bg-success-soft text-success',
}
const SOURCE_BADGE: Record<string, string> = {
  generated: 'bg-primary-soft/70 text-primary',
  manual: 'bg-surface-2 text-muted',
  recovered: 'bg-warning-soft text-warning',
}
const BLOCK_FA: Record<string, string> = { school: 'مدرسه', class: 'کلاس', free: 'وقت آزاد' }
const BLOCK_STYLE: Record<string, string> = {
  school: 'bg-warning-soft text-warning',
  class: 'bg-review-soft text-review',
  free: 'bg-success-soft text-success',
}

export function PlanPage() {
  const qc = useQueryClient()
  const todayQ = useQuery({ queryKey: ['today'], queryFn: () => api.get<TodayOut>('/today') })
  const [selected, setSelected] = useState<string | null>(null)
  const day = selected ?? todayQ.data?.date ?? null

  const dayQ = useQuery({
    queryKey: ['plan-day', day],
    queryFn: () => api.get<PlanDayOut>(`/plans/${day}`),
    enabled: !!day,
  })
  const blocksQ = useQuery({
    queryKey: ['time-blocks', day],
    queryFn: () => api.get<TimeBlocksOut>(`/time-blocks?date=${day}`),
    enabled: !!day,
  })

  const [lastRun, setLastRun] = useState<GenerateWeekOut | null>(null)
  const [recoverOut, setRecoverOut] = useState<RecoveryOut | null>(null)
  const [mergeMode, setMergeMode] = useState(false)
  const [mergeIds, setMergeIds] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ['today'] })
    qc.invalidateQueries({ queryKey: ['plan-day'] })
    qc.invalidateQueries({ queryKey: ['time-blocks'] })
  }
  const onErr = (e: unknown) => setError(e instanceof ApiError ? e.message : 'خطای نامشخص.')

  const genM = useMutation({
    mutationFn: () => api.post<GenerateWeekOut>('/plans/generate-week', {}),
    onSuccess: (data) => { setLastRun(data); setRecoverOut(null); setError(null); invalidateAll() },
    onError: onErr,
  })
  const recM = useMutation({
    mutationFn: () => api.post<RecoveryOut>('/plans/recover', {}),
    onSuccess: (data) => { setRecoverOut(data); setError(null); invalidateAll() },
    onError: onErr,
  })
  const statusM = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'done' | 'pending' | 'skipped' }) =>
      api.post<PlanTaskOut>(`/plans/tasks/${id}/status`, { status }),
    onSuccess: invalidateAll, onError: onErr,
  })
  const lockM = useMutation({
    mutationFn: ({ id, locked }: { id: string; locked: boolean }) =>
      api.post<PlanTaskOut>(`/plans/tasks/${id}/lock`, { locked }),
    onSuccess: invalidateAll, onError: onErr,
  })
  const splitM = useMutation({
    mutationFn: ({ id, parts }: { id: string; parts: number[] }) =>
      api.post<{ parts: number; tasks: PlanTaskOut[] }>(`/plans/tasks/${id}/split`, { parts }),
    onSuccess: invalidateAll, onError: onErr,
  })
  const mergeM = useMutation({
    mutationFn: (ids: string[]) => api.post<PlanTaskOut>('/plans/tasks/merge', { task_ids: ids }),
    onSuccess: () => { setMergeMode(false); setMergeIds([]); invalidateAll() },
    onError: onErr,
  })
  const moveM = useMutation({
    mutationFn: ({ from, taskId, to }: { from: string; taskId: string; to: string }) =>
      api.post<PlanTaskOut>(`/plans/${from}/move-task`, { task_id: taskId, to_date: to }),
    onSuccess: invalidateAll, onError: onErr,
  })
  const putDayM = useMutation({
    mutationFn: ({ date, tasks }: { date: string; tasks: PlanTaskIn[] }) =>
      api.put<PlanDayOut>(`/plans/${date}`, { tasks }),
    onSuccess: invalidateAll, onError: onErr,
  })
  const putBlocksM = useMutation({
    mutationFn: ({ date, blocks }: { date: string; blocks: TimeBlockIn[] }) =>
      api.put<TimeBlocksOut>('/time-blocks', { date, blocks }),
    onSuccess: invalidateAll, onError: onErr,
  })
  const schoolOffM = useMutation({
    mutationFn: (date: string) => api.post<TimeBlocksOut>('/school-override', { date, school_off: true }),
    onSuccess: invalidateAll, onError: onErr,
  })

  const weekDays = todayQ.data?.week.days ?? []
  const tasks = dayQ.data?.tasks ?? []
  const cap = dayQ.data?.capacity

  if (todayQ.isPending) {
    return (
      <Page title="برنامه">
        <div className="flex flex-col items-center gap-3 py-20 text-muted">
          <Spinner />
          <span className="text-body-sm">در حال بارگذاری هفته…</span>
        </div>
      </Page>
    )
  }

  return (
    <Page title="برنامه هفته" subtitle="هفته شنبه تا جمعه — برنامه یک پیشنهاد است؛ ویرایش دستی تو همیشه برنده است (§۸.۷)">
      <div className="flex flex-col gap-4">
        {error && (
          <motion.div variants={fadeInUp} initial="initial" animate="animate" className="rounded-md bg-danger-soft px-4 py-2.5 text-body-sm text-danger">
            {error}
          </motion.div>
        )}

        {/* دکمه‌های هفته */}
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => genM.mutate()} disabled={genM.isPending}>
            {genM.isPending ? 'در حال ساخت…' : 'ساخت برنامه هفته'}
          </Button>
          <Button variant="soft" onClick={() => recM.mutate()} disabled={recM.isPending}>
            {recM.isPending ? 'در حال جبران…' : 'جبران عقب‌افتادگی‌ها'}
          </Button>
          {lastRun && (
            <span className="text-body-sm text-muted">
              آخرین اجرا: {faDigits(lastRun.created)} کار جدید · {faDigits(lastRun.removed)} پیشنهاد قبلی حذف شد ·{' '}
              <strong className="text-success">{faDigits(lastRun.kept_locked)} کار قفل‌شده حفظ شد</strong>
            </span>
          )}
        </div>

        {/* انیمیشن pipeline هنگام تولید (doc 07.4 #8) */}
        <AnimatePresence>
          {genM.isPending && (
            <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit">
              <Card className="p-4">
                <p className="mb-2 text-body-sm font-semibold text-muted">planner در حال کار — ۱۲ مرحله:</p>
                <ul className="grid grid-cols-2 gap-x-4 gap-y-1 md:grid-cols-3">
                  {PIPELINE_FA.map(([key, label], i) => (
                    <motion.li key={key} custom={i} variants={plannerStep} initial="initial" animate="animate" className="flex items-center gap-2 text-body-sm">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary-soft text-[10px] font-bold text-primary">
                        {faDigits(i + 1)}
                      </span>
                      {label}
                    </motion.li>
                  ))}
                </ul>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* نتیجه recovery — V2-P04: پخش بین روزهای باقی‌مانده، نه همه روی فردا */}
        <AnimatePresence>
          {recoverOut && (
            <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit">
              <Card className="border-warning/40 bg-warning-soft/30 p-4">
                <p className="text-body-sm font-semibold">
                  {faDigits(recoverOut.moved)} کار عقب‌افتاده جابه‌جا شد — سهم فردا/امروز فقط{' '}
                  {faDigits(recoverOut.tomorrow_share)} کار؛ بقیه بین روزهای هفته پخش شد.
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {Object.entries(recoverOut.days).map(([dte, n]) => (
                    <span key={dte} className="rounded-md bg-surface px-2 py-0.5 text-[11px] text-muted">
                      {dte}: {faDigits(n)}
                    </span>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* نوار هفته */}
        {weekDays.length > 0 && (
          <div className="grid grid-cols-7 gap-1.5">
            {weekDays.map((w) => (
              <button
                key={w.date}
                type="button"
                onClick={() => { setSelected(w.date); setMergeMode(false); setMergeIds([]) }}
                className={[
                  'flex flex-col items-center gap-0.5 rounded-md border px-1 py-2 transition-colors',
                  w.date === day
                    ? 'border-primary bg-primary-soft'
                    : w.is_today
                      ? 'border-primary/40 bg-surface hover:bg-surface-2'
                      : 'border-border bg-surface hover:bg-surface-2',
                ].join(' ')}
              >
                <span className="text-[10px] text-muted">{w.weekday_fa}</span>
                <span className="text-body-sm font-bold">{faDigits(w.date_jalali)}</span>
                <span className="text-[10px] text-muted">
                  {faDigits(w.done_count)}/{faDigits(w.tasks_count)} کار
                  {w.locked_count > 0 ? ` · ${faDigits(w.locked_count)}🔓` : ''}
                </span>
              </button>
            ))}
          </div>
        )}

        {/* پنل روز */}
        {dayQ.isPending ? (
          <Card className="flex items-center justify-center p-8"><Spinner /></Card>
        ) : dayQ.isError || !dayQ.data ? (
          <EmptyState icon="plan" text={dayQ.error instanceof ApiError ? dayQ.error.message : 'خطا در بارگذاری روز.'} />
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="flex flex-col gap-4 lg:col-span-2">
              <DayTasks
                data={dayQ.data}
                mergeMode={mergeMode}
                mergeIds={mergeIds}
                setMergeMode={(v) => { setMergeMode(v); setMergeIds([]) }}
                setMergeIds={setMergeIds}
                busy={statusM.isPending || lockM.isPending || splitM.isPending || moveM.isPending || putDayM.isPending}
                onStatus={(id, status) => statusM.mutate({ id, status })}
                onLock={(id, locked) => lockM.mutate({ id, locked })}
                onSplit={(id, parts) => splitM.mutate({ id, parts })}
                onMove={(taskId, to) => moveM.mutate({ from: day!, taskId, to })}
                onDelete={(t) => putDayM.mutate({
                  date: day!,
                  tasks: tasks.filter((x) => x.id !== t.id).map((x) => ({ id: x.id, locked: x.locked })),
                })}
                onAdd={(entry) => putDayM.mutate({
                  date: day!,
                  tasks: [...tasks.map((x) => ({ id: x.id, locked: x.locked } as PlanTaskIn)), entry],
                })}
                onMerge={() => mergeM.mutate(mergeIds)}
                weekDays={weekDays.map((w) => ({ date: w.date, label: `${w.weekday_fa} ${w.date_jalali}` }))}
              />
            </div>
            <div className="flex flex-col gap-4">
              <CapacityCard cap={cap} counts={dayQ.data.counts} />
              <BlocksCard
                blocks={blocksQ.data?.blocks ?? []}
                loading={blocksQ.isPending}
                busy={putBlocksM.isPending || schoolOffM.isPending}
                onAdd={(b) => putBlocksM.mutate({
                  date: day!,
                  blocks: [
                    ...(blocksQ.data?.blocks ?? []).map((x: TimeBlockOut) => ({ kind: x.kind, start: x.start, end: x.end, title: x.title ?? undefined })),
                    b,
                  ],
                })}
                onRemove={(bid) => putBlocksM.mutate({
                  date: day!,
                  blocks: (blocksQ.data?.blocks ?? []).filter((x) => x.id !== bid).map((x) => ({ kind: x.kind, start: x.start, end: x.end, title: x.title ?? undefined })),
                })}
                onSchoolOff={() => schoolOffM.mutate(day!)}
              />
            </div>
          </div>
        )}
      </div>
    </Page>
  )
}

/* --- ظرفیت روز ------------------------------------------------------------------ */

function CapacityCard({ cap, counts }: { cap: CapacityOut | undefined; counts: PlanDayOut['counts'] }) {
  if (!cap) return null
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center gap-2">
        <Icon name="clock" size={17} />
        <h2 className="text-title-sm font-bold">ظرفیت روز</h2>
        {cap.source === 'override' && (
          <span className="mr-auto rounded-md bg-warning-soft px-2 py-0.5 text-[11px] font-semibold text-warning">override</span>
        )}
      </div>
      <dl className="flex flex-col gap-1.5 text-body-sm">
        <Row k="زمان آزاد مطالعه" v={`${faDigits(cap.available_minutes)} دقیقه`} />
        <Row k="مدرسه" v={`${faDigits(cap.school_minutes)} دقیقه`} />
        <Row k="کلاس" v={`${faDigits(cap.class_minutes)} دقیقه`} />
        <Row k="کار پیشنهادی" v={faDigits(cap.suggested_task_count)} />
        <Row k="وعده پیشنهادی" v={`${faDigits(cap.suggested_session_count)} وعده`} />
        <Row k="انجام ۷ روز اخیر" v={`${faDigits(Math.round(cap.completion_rate * 100))}٪`} />
        <Row k="دقیقه برنامه‌ریزی‌شده" v={`${faDigits(counts.minutes)} دقیقه`} />
      </dl>
      <p className="mt-3 text-[11px] leading-5 text-muted">
        وقت آزاد با ظرفیت فرق دارد — ظرفیت یعنی بخشی از وقت آزاد که واقعاً به مطالعه می‌رسد.
      </p>
    </Card>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <dt className="text-muted">{k}</dt>
      <dd className="font-semibold">{v}</dd>
    </div>
  )
}

/* --- بلوک‌های زمانی (doc 11.2 ورودی ظرفیت) ---------------------------------------- */

function BlocksCard({ blocks, loading, busy, onAdd, onRemove, onSchoolOff }: {
  blocks: TimeBlockOut[]
  loading: boolean
  busy: boolean
  onAdd: (b: TimeBlockIn) => void
  onRemove: (id: string) => void
  onSchoolOff: () => void
}) {
  const [kind, setKind] = useState<'school' | 'class' | 'free'>('free')
  const [start, setStart] = useState('16:00')
  const [end, setEnd] = useState('18:00')
  const [title, setTitle] = useState('')

  const submit = () => {
    onAdd({ kind, start, end, title: title.trim() || undefined })
    setTitle('')
  }
  const hasSchool = blocks.some((b) => b.kind === 'school')

  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center gap-2">
        <Icon name="sun" size={17} />
        <h2 className="text-title-sm font-bold">بلوک‌های زمانی</h2>
      </div>
      {loading ? (
        <div className="flex justify-center py-4"><Spinner /></div>
      ) : blocks.length === 0 ? (
        <p className="text-body-sm text-muted">بلوکی ثبت نشده — از پیش‌فرض روز استفاده می‌شود.</p>
      ) : (
        <ul className="mb-3 flex flex-col gap-1.5">
          {blocks.map((b) => (
            <li key={b.id} className="flex items-center gap-2 rounded-md bg-surface-2/70 px-2.5 py-2">
              <span className={['rounded-md px-1.5 py-0.5 text-[10px] font-semibold', BLOCK_STYLE[b.kind]].join(' ')}>
                {BLOCK_FA[b.kind] ?? b.kind}
              </span>
              <span className="text-body-sm font-medium">{faDigits(b.start)}–{faDigits(b.end)}</span>
              {b.title && <span className="truncate text-[11px] text-muted">{b.title}</span>}
              <span className="mr-auto text-[11px] text-muted">{faDigits(b.minutes)}د</span>
              <ConfirmButton
                onConfirm={() => onRemove(b.id)}
                busy={busy}
                label="✕"
                confirmLabel="بلوک حذف شود؟"
                className="!px-2 !py-0.5 !text-[11px]"
              />
            </li>
          ))}
        </ul>
      )}
      <div className="flex flex-col gap-2">
        <div className="flex gap-1.5">
          {(['school', 'class', 'free'] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setKind(k)}
              className={[
                'flex-1 rounded-md px-2 py-1.5 text-[11px] font-semibold transition-colors',
                kind === k ? BLOCK_STYLE[k] : 'bg-surface-2 text-muted hover:text-ink',
              ].join(' ')}
            >
              {BLOCK_FA[k]}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input
            value={start} onChange={(e) => setStart(e.target.value)} placeholder="۰۸:۰۰"
            className="w-20 rounded-md border border-border bg-surface px-2 py-1.5 text-body-sm" dir="ltr" aria-label="شروع"
          />
          <span className="text-muted">→</span>
          <input
            value={end} onChange={(e) => setEnd(e.target.value)} placeholder="۱۴:۰۰"
            className="w-20 rounded-md border border-border bg-surface px-2 py-1.5 text-body-sm" dir="ltr" aria-label="پایان"
          />
          <input
            value={title} onChange={(e) => setTitle(e.target.value)} placeholder="عنوان (اختیاری)"
            className="min-w-0 flex-1 rounded-md border border-border bg-surface px-2 py-1.5 text-body-sm" aria-label="عنوان بلوک"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="soft" onClick={submit} disabled={busy}>افزودن بلوک</Button>
          {hasSchool && (
            <Button variant="ghost" onClick={onSchoolOff} disabled={busy}>امروز مدرسه تعطیل است</Button>
          )}
        </div>
      </div>
    </Card>
  )
}

/* --- کارهای روز + overrideها (doc 11.4) ------------------------------------------- */

function DayTasks({ data, mergeMode, mergeIds, setMergeMode, setMergeIds, busy, onStatus, onLock, onSplit, onMove, onDelete, onAdd, onMerge, weekDays }: {
  data: PlanDayOut
  mergeMode: boolean
  mergeIds: string[]
  setMergeMode: (v: boolean) => void
  setMergeIds: (v: string[]) => void
  busy: boolean
  onStatus: (id: string, status: 'done' | 'pending' | 'skipped') => void
  onLock: (id: string, locked: boolean) => void
  onSplit: (id: string, parts: number[]) => void
  onMove: (taskId: string, to: string) => void
  onDelete: (t: PlanTaskOut) => void
  onAdd: (entry: PlanTaskIn) => void
  onMerge: () => void
  weekDays: { date: string; label: string }[]
}) {
  const [title, setTitle] = useState('')
  const [minutes, setMinutes] = useState(45)
  const [kind, setKind] = useState<'study' | 'test' | 'review' | 'goal'>('study')

  const toggleMerge = (id: string) =>
    setMergeIds(mergeIds.includes(id) ? mergeIds.filter((x) => x !== id) : [...mergeIds, id])

  const addTask = () => {
    if (!title.trim()) return
    onAdd({ title: title.trim(), kind, minutes })
    setTitle('')
  }

  return (
    <Card className="p-4 md:p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="text-title-sm font-bold">{data.weekday_fa} {faDigits(data.date_jalali)}</h2>
        <span className="text-body-sm text-muted">
          {faDigits(data.counts.total)} کار · {faDigits(data.counts.done)} انجام · {faDigits(data.counts.minutes)} دقیقه
        </span>
        <div className="mr-auto flex gap-2">
          {data.tasks.length >= 2 && (
            <Button variant={mergeMode ? 'primary' : 'ghost'} onClick={() => setMergeMode(!mergeMode)}>
              {mergeMode ? 'حالت ادغام: روشن' : 'ادغام کارها'}
            </Button>
          )}
        </div>
      </div>

      <AnimatePresence>
        {mergeMode && (
          <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit" className="mb-3 flex items-center gap-2 rounded-md bg-surface-2 px-3 py-2">
            <span className="text-body-sm text-muted">{faDigits(mergeIds.length)} کار انتخاب شده — کارهای هم‌روز با هم ادغام می‌شوند.</span>
            <Button className="mr-auto" disabled={mergeIds.length < 2 || busy} onClick={onMerge}>ادغام کن</Button>
            <Button variant="ghost" onClick={() => setMergeMode(false)}>انصراف</Button>
          </motion.div>
        )}
      </AnimatePresence>

      {data.tasks.length === 0 ? (
        <EmptyState icon="plan" text="این روز خالی است — دستی کار اضافه کن یا هفته را از نو بساز." />
      ) : (
        <motion.ul variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-1.5">
          {data.tasks.map((t) => (
            <TaskRow
              key={t.id}
              task={t}
              mergeMode={mergeMode}
              selected={mergeIds.includes(t.id)}
              onToggleMerge={() => toggleMerge(t.id)}
              busy={busy}
              onStatus={onStatus}
              onLock={onLock}
              onSplit={onSplit}
              onMove={onMove}
              onDelete={onDelete}
              weekDays={weekDays.filter((w) => w.date !== data.date)}
            />
          ))}
        </motion.ul>
      )}

      {/* افزودن کار دستی — manual override همیشه برنده است (§8.7) */}
      <div className="mt-4 rounded-md bg-surface-2 p-3">
        <p className="mb-2 text-body-sm font-semibold">افزودن کار دستی</p>
        <div className="flex flex-wrap items-center gap-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addTask()}
            placeholder="مثلاً: مرور فصل ۲ ریاضی"
            className="min-w-40 flex-1 rounded-md border border-border bg-surface px-3 py-2 text-body-sm"
            aria-label="عنوان کار"
          />
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as typeof kind)}
            className="rounded-md border border-border bg-surface px-2 py-2 text-body-sm"
            aria-label="نوع کار"
          >
            <option value="study">مطالعه</option>
            <option value="test">تست</option>
            <option value="review">مرور</option>
            <option value="goal">هدف</option>
          </select>
          <input
            type="number" min={5} max={600} value={minutes}
            onChange={(e) => setMinutes(Number(e.target.value))}
            className="w-20 rounded-md border border-border bg-surface px-2 py-2 text-body-sm"
            aria-label="دقیقه"
          />
          <Button onClick={addTask} disabled={busy || !title.trim()}>افزودن</Button>
        </div>
      </div>
    </Card>
  )
}

function TaskRow({ task, mergeMode, selected, onToggleMerge, busy, onStatus, onLock, onSplit, onMove, onDelete, weekDays }: {
  task: PlanTaskOut
  mergeMode: boolean
  selected: boolean
  onToggleMerge: () => void
  busy: boolean
  onStatus: (id: string, status: 'done' | 'pending' | 'skipped') => void
  onLock: (id: string, locked: boolean) => void
  onSplit: (id: string, parts: number[]) => void
  onMove: (taskId: string, to: string) => void
  onDelete: (t: PlanTaskOut) => void
  weekDays: { date: string; label: string }[]
}) {
  const [open, setOpen] = useState(false)
  const [p1, setP1] = useState(Math.floor(task.minutes / 2))
  const done = task.status === 'done'

  return (
    <motion.li variants={listItem} className={['rounded-md border px-2.5 py-2', selected ? 'border-primary bg-primary-soft/40' : 'border-transparent hover:border-border'].join(' ')}>
      <div className="flex items-center gap-2.5">
        {mergeMode ? (
          <input type="checkbox" checked={selected} onChange={onToggleMerge} className="h-4 w-4 shrink-0 accent-[var(--color-primary)]" aria-label="انتخاب برای ادغام" />
        ) : (
          <button
            type="button"
            disabled={busy}
            onClick={() => onStatus(task.id, done ? 'pending' : 'done')}
            aria-label={done ? 'برگردان' : 'انجام شد'}
            className={[
              'flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full border-2 transition-colors',
              done ? 'border-success bg-success text-white' : 'border-border hover:border-primary',
            ].join(' ')}
          >
            {done && <Icon name="check" size={13} />}
          </button>
        )}
        <div className="min-w-0 flex-1">
          <p className={['truncate text-body-sm font-medium', done ? 'text-muted line-through' : ''].join(' ')}>{task.title}</p>
          <p className="truncate text-[11px] text-muted">
            {faDigits(task.minutes)} دقیقه
            {task.count ? ` · ${faDigits(task.count)} آیتم` : ''}
            {task.topic_title ? ` · ${task.topic_title}` : ''}
            {task.reason_fa ? ` · ${task.reason_fa}` : ''}
          </p>
        </div>
        <span className={['shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-semibold', KIND_BADGE[task.kind] ?? 'bg-surface-2 text-muted'].join(' ')}>
          {task.kind_fa}
        </span>
        <span className={['hidden shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-semibold sm:inline', SOURCE_BADGE[task.source] ?? 'bg-surface-2 text-muted'].join(' ')}>
          {task.source_fa}
        </span>
        {!mergeMode && (
          <>
            <button
              type="button" disabled={busy}
              onClick={() => onLock(task.id, !task.locked)}
              className={[
                'shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-semibold transition-colors',
                task.locked ? 'bg-warning-soft text-warning' : 'bg-surface-2 text-muted hover:text-ink',
              ].join(' ')}
              aria-label={task.locked ? 'باز کردن قفل' : 'قفل کردن'}
            >
              {task.locked ? 'قفل ✓' : 'قفل'}
            </button>
            <button type="button" onClick={() => setOpen(!open)} className="shrink-0 px-1 text-muted hover:text-ink" aria-label="عملیات بیشتر">
              <Icon name="more" size={16} />
            </button>
          </>
        )}
      </div>

      <AnimatePresence>
        {open && !mergeMode && (
          <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit" className="mt-2 flex flex-wrap items-center gap-2 border-t border-border pt-2">
            {/* split */}
            <span className="text-[11px] text-muted">تقسیم:</span>
            <input
              type="number" min={10} value={p1} onChange={(e) => setP1(Number(e.target.value))}
              className="w-16 rounded-md border border-border bg-surface px-1.5 py-1 text-[11px]" aria-label="بخش اول"
            />
            <span className="text-[11px] text-muted">+ {faDigits(Math.max(task.minutes - p1, 0))} دقیقه</span>
            <Button
              variant="soft"
              className="!px-2.5 !py-1 !text-[11px]"
              disabled={busy || p1 < 10 || task.minutes - p1 < 10}
              onClick={() => { onSplit(task.id, [p1, task.minutes - p1]); setOpen(false) }}
            >
              تقسیم
            </Button>
            {/* move */}
            <span className="text-[11px] text-muted">انتقال به:</span>
            <select
              className="rounded-md border border-border bg-surface px-1.5 py-1 text-[11px]"
              defaultValue=""
              aria-label="انتقال به روز"
              onChange={(e) => { if (e.target.value) { onMove(task.id, e.target.value); setOpen(false) } }}
              disabled={busy}
            >
              <option value="" disabled>روز دیگر…</option>
              {weekDays.map((w) => <option key={w.date} value={w.date}>{w.label}</option>)}
            </select>
            {/* skip + delete */}
            <Button variant="ghost" className="!px-2.5 !py-1 !text-[11px]" disabled={busy} onClick={() => { onStatus(task.id, task.status === 'skipped' ? 'pending' : 'skipped'); setOpen(false) }}>
              {task.status === 'skipped' ? 'برگرداندن از رد' : 'رد کردن'}
            </Button>
            {/* عملیات مخرب → تأیید دومرحله‌ای (doc 07.9) */}
            <ConfirmButton
              onConfirm={() => { onDelete(task); setOpen(false) }}
              busy={busy}
              disabled={busy || task.locked}
              label="حذف"
              confirmLabel="کار حذف شود؟"
              className="!px-2.5 !py-1 !text-[11px]"
            />
            {task.locked && <span className="text-[10px] text-warning">کار قفل‌شده حذف نمی‌شود — اول قفل را باز کن.</span>}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.li>
  )
}
