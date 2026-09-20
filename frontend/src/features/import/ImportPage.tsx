/**
 * Import — صفحه وارد کردن کتاب از فایل JSON (فاز ۲، doc 09 §9.1).
 *
 * - drag/drop فایل JSON + انتخاب فایل + چسباندن متن
 * - TOC-only: فایل بدون هیچ سوال کاملاً معتبر است (doc 08 §8.3.1) —
 *   هیچ بررسی «حداقل یک سوال» سمت client هم وجود ندارد
 * - پیش‌نمایش شمارش فصل/موضوع/سوال قبل از ارسال
 * - duplicate (title+publisher) → 409 با گزینه جایگزینی (replace=true)
 * - راهنمای ساختار فایل از GET /resources/import-book/schema
 */
import { useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../lib/api'
import type { ImportResult, ImportSchema } from '../../lib/schemas'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { Button } from '../../components/Button'
import { BlockTypeBadge } from '../../components/BlockTypeBadge'
import { Icon } from '../../components/Icon'
import { Spinner } from '../../components/Spinner'
import { faDigits } from '../../lib/dates'
import { D, EASE_OUT, fadeInUp, staggerList, listItem, successPulse } from '../../motion/variants'

/* eslint-disable @typescript-eslint/no-explicit-any */

const EXAMPLE = {
  title: 'شیمی ۲',
  publisher: 'مبتکران',
  subject: 'شیمی',
  chapters: [
    {
      title: 'فصل ۱',
      topics: [
        {
          title: 'الگوها و روندها',
          block_type: 'topic',
          subtopics: [{ title: 'جدول دوره‌ای' }],
        },
        { title: 'کنکور ۱۴۰۳' },
        { title: 'آزمون فصل ۱' },
      ],
    },
  ],
}

interface Preview {
  title: string
  publisher: string
  subject: string | null
  counts: { chapters: number; topics: number; questions: number }
}

function countPayload(d: any): Preview['counts'] {
  let chapters = 0
  let topics = 0
  let questions = 0
  const walkTopic = (t: any) => {
    topics += 1
    questions += (t?.questions || []).length
    for (const sub of t?.subtopics || []) walkTopic(sub)
  }
  for (const ch of d?.chapters || []) {
    chapters += 1
    questions += (ch?.questions || []).length
    for (const t of [...(ch?.topics || []), ...(ch?.subtopics || [])]) walkTopic(t)
  }
  for (const t of d?.topics || []) walkTopic(t)
  return { chapters, topics, questions }
}

/** پیش‌اعتبارسنجی سمت client — دقیقاً مثل backend: TOC-only معتبر است. */
function parsePreview(raw: string): { preview?: Preview; parsed?: any; error?: string } {
  if (!raw.trim()) return {}
  let parsed: any
  try {
    parsed = JSON.parse(raw)
  } catch {
    return { error: 'فایل JSON معتبر نیست — کاراکتر یا براکت نابجا را اصلاح کن.' }
  }
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    return { error: 'محتوا باید یک آبجکت JSON باشد (نه آرایه).' }
  }
  const title = String(parsed.title ?? '').trim()
  if (!title) return { parsed, error: 'عنوان کتاب الزامی است.' }
  return {
    parsed,
    preview: {
      title,
      publisher: String(parsed.publisher ?? '').trim(),
      subject: parsed.subject ? String(parsed.subject).trim() : null,
      counts: countPayload(parsed),
    },
  }
}

export function ImportPage() {
  const qc = useQueryClient()
  const [raw, setRaw] = useState('')
  const [fileName, setFileName] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [conflict, setConflict] = useState<any | null>(null) // payload در انتظار 409
  const [result, setResult] = useState<ImportResult | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const { preview, error: parseError } = useMemo(() => parsePreview(raw), [raw])

  const { data: schema } = useQuery({
    queryKey: ['import-schema'],
    queryFn: () => api.get<ImportSchema>('/resources/import-book/schema'),
  })

  const handleFile = async (file: File) => {
    setResult(null)
    setConflict(null)
    setFormError(null)
    setFileName(file.name)
    try {
      setRaw(await file.text())
    } catch {
      setFormError('خواندن فایل ممکن نشد؛ دوباره تلاش کن.')
    }
  }

  const submit = async (payload: any) => {
    setBusy(true)
    setFormError(null)
    try {
      const res = await api.post<ImportResult>('/resources/import-book', payload)
      qc.invalidateQueries({ queryKey: ['resources'] })
      qc.invalidateQueries({ queryKey: ['resource-tree'] })
      setResult(res)
      setConflict(null)
      setRaw('')
      setFileName(null)
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setConflict(payload) // duplicate → گزینه به‌روزرسانی (doc 08 §8.3.5)
      } else {
        setFormError(e instanceof ApiError ? e.message : 'ارسال ناموفق بود؛ دوباره تلاش کن.')
      }
    } finally {
      setBusy(false)
    }
  }

  const onSubmit = () => {
    const { parsed, error } = parsePreview(raw)
    if (error || !parsed) {
      setFormError(error || 'محتوایی برای ارسال نیست.')
      return
    }
    void submit(parsed)
  }

  const reset = () => {
    setResult(null)
    setConflict(null)
    setFormError(null)
    setRaw('')
    setFileName(null)
  }

  return (
    <Page title="وارد کردن کتاب" subtitle="فایل JSON فهرست کتاب را رها کن — بدون سوال هم معتبر است (TOC-only)">
      <motion.div variants={staggerList} initial="initial" animate="animate" className="flex flex-col gap-4">
        {/* نتیجه موفق */}
        <AnimatePresence>
          {result && (
            <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit">
              <Card className="flex flex-col items-center gap-3 p-6 text-center">
                <motion.div variants={successPulse} initial="initial" animate="animate" className="flex h-14 w-14 items-center justify-center rounded-full bg-success-soft text-success">
                  <Icon name="check" size={28} />
                </motion.div>
                <div>
                  <p className="text-title-sm font-bold">
                    «{result.resource.title}» {result.replaced ? 'جایگزین شد' : 'وارد شد'}
                  </p>
                  <p className="mt-1 text-body-sm text-muted">
                    {faDigits(result.resource.counts.chapters)} فصل · {faDigits(result.resource.counts.topics)} موضوع ·{' '}
                    {result.resource.counts.questions === 0
                      ? 'بدون سوال (TOC-only) ✓'
                      : `${faDigits(result.resource.counts.questions)} سوال`}
                  </p>
                </div>
                <div className="mt-1 flex flex-wrap items-center justify-center gap-2">
                  <Button to="/study">دیدن درخت کتاب</Button>
                  <Button variant="ghost" onClick={reset}>وارد کردن کتاب دیگر</Button>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* drop zone */}
        <motion.div variants={listItem}>
          <Card className="p-4 md:p-5">
            <div
              role="button"
              tabIndex={0}
              aria-label="رها کردن یا انتخاب فایل JSON"
              onClick={() => fileRef.current?.click()}
              onKeyDown={(e) => e.key === 'Enter' && fileRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragging(false)
                const f = e.dataTransfer.files?.[0]
                if (f) void handleFile(f)
              }}
              className={[
                'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
                dragging ? 'border-primary bg-primary-soft' : 'border-border bg-surface-2/40 hover:border-primary/50',
              ].join(' ')}
            >
              <motion.div animate={{ scale: dragging ? 1.08 : 1 }} transition={{ duration: D.fast, ease: EASE_OUT }} className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Icon name="book-open" size={26} />
              </motion.div>
              <div>
                <p className="text-body font-semibold">فایل JSON را اینجا رها کن</p>
                <p className="mt-1 text-body-sm text-muted">یا کلیک کن و فایل را انتخاب کن — چسباندن متن هم پایین‌تر ممکن است</p>
              </div>
              <input
                ref={fileRef}
                type="file"
                accept=".json,application/json"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) void handleFile(f)
                  e.target.value = ''
                }}
              />
            </div>

            {(fileName || raw) && (
              <div className="mt-3 flex items-center justify-between gap-2 rounded-md bg-surface-2 px-3 py-2">
                <span className="min-w-0 truncate text-body-sm text-muted" dir="ltr">
                  {fileName ?? 'چسبانده شد'}
                </span>
                <button onClick={reset} className="shrink-0 text-body-sm text-danger hover:underline">
                  پاک کردن
                </button>
              </div>
            )}

            {/* paste area */}
            <label htmlFor="import-json" className="mt-4 block text-body-sm font-semibold text-muted">
              یا متن JSON را بچسبان
            </label>
            <textarea
              id="import-json"
              value={raw}
              onChange={(e) => {
                setRaw(e.target.value)
                setResult(null)
                setConflict(null)
              }}
              dir="ltr"
              spellCheck={false}
              rows={8}
              placeholder='{"title": "شیمی ۲", "publisher": "مبتکران", "chapters": [...]}'
              className="mt-2 w-full rounded-md border border-border bg-surface p-3 text-left font-mono text-body-sm text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-primary"
            />

            {/* خطای parse */}
            <AnimatePresence>
              {parseError && (
                <motion.p variants={fadeInUp} initial="initial" animate="animate" exit="exit" role="alert" className="mt-2 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger">
                  {parseError}
                </motion.p>
              )}
            </AnimatePresence>

            {/* پیش‌نمایش */}
            <AnimatePresence>
              {preview && (
                <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit" className="mt-3 rounded-md border border-border bg-surface-2/50 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-body font-bold">{preview.title}</span>
                    {preview.publisher && <span className="text-body-sm text-muted">— {preview.publisher}</span>}
                    {preview.subject && <span className="text-body-sm text-muted">({preview.subject})</span>}
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-body-sm">
                    <span className="rounded-md bg-surface px-2 py-0.5 text-muted">{faDigits(preview.counts.chapters)} فصل</span>
                    <span className="rounded-md bg-surface px-2 py-0.5 text-muted">{faDigits(preview.counts.topics)} موضوع</span>
                    <span className="rounded-md bg-surface px-2 py-0.5 text-muted">{faDigits(preview.counts.questions)} سوال</span>
                    {preview.counts.questions === 0 && (
                      <span className="rounded-md bg-success-soft px-2 py-0.5 font-semibold text-success">
                        فقط فهرست (TOC-only) — معتبر است
                      </span>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* خطای ارسال */}
            <AnimatePresence>
              {formError && (
                <motion.p variants={fadeInUp} initial="initial" animate="animate" exit="exit" role="alert" className="mt-3 rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger">
                  {formError}
                </motion.p>
              )}
            </AnimatePresence>

            {/* 409 → گزینه به‌روزرسانی */}
            <AnimatePresence>
              {conflict && (
                <motion.div variants={fadeInUp} initial="initial" animate="animate" exit="exit" className="mt-3 flex flex-col gap-3 rounded-md border border-warning/40 bg-warning-soft p-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-body-sm font-semibold text-warning" role="alert">
                    این کتاب قبلاً وارد شده است. جایگزینش کنی، نسخه قبلی (با وضعیت آموزش‌دیده) پاک می‌شود.
                  </p>
                  <div className="flex shrink-0 gap-2">
                    <Button variant="primary" disabled={busy} onClick={() => void submit({ ...conflict, replace: true })}>
                      جایگزینی کن
                    </Button>
                    <Button variant="ghost" onClick={() => setConflict(null)}>
                      بی‌خیال
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Button onClick={onSubmit} disabled={busy || !preview}>
                {busy ? <Spinner size={16} /> : <Icon name="book-open" size={16} />}
                وارد کردن کتاب
              </Button>
              <Button variant="ghost" onClick={() => { reset(); setRaw(JSON.stringify(EXAMPLE, null, 2)) }}>
                بارگذاری نمونه
              </Button>
            </div>
          </Card>
        </motion.div>

        {/* راهنمای ساختار — از API واقعی schema */}
        {schema && (
          <motion.div variants={listItem}>
            <Card className="p-4 md:p-5">
              <h2 className="text-title-sm font-bold">راهنمای ساختار فایل</h2>
              <p className="mt-1 text-body-sm text-muted">{schema.description}</p>

              <ul className="mt-3 flex list-disc flex-col gap-1.5 pr-5 text-body-sm text-muted">
                {schema.rules.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>

              <div className="mt-4">
                <h3 className="text-body-sm font-bold">انواع بلوک (block_type)</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {schema.block_types.map((b) => (
                    <BlockTypeBadge key={b.value} type={b.value} label={b.label_fa} />
                  ))}
                </div>
                <p className="mt-2 text-body-sm text-muted">
                  اگر block_type نیاید، از عنوان استنتاج می‌شود:
                </p>
                <ul className="mt-1 flex list-disc flex-col gap-1 pr-5 text-body-sm text-muted">
                  {schema.block_type_inference.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            </Card>
          </motion.div>
        )}
      </motion.div>
    </Page>
  )
}
