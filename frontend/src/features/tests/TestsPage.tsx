// صفحه تست‌ها — وارد کردن کتاب، ثبت سریع تست، دفترچه خطا
import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, errorMessage, get, post } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, Modal, PageHeader, PercentBar, Spinner } from '../../components/ui';
import {
  DIFFICULTY_LABELS, ERROR_TYPE_LABELS, MARK_COLORS, MARK_LABELS,
  type MarkType, type Question, type Resource, type TestRecord, type TestResult,
} from '../../types';
import { faNumber, formatJalali, toFaDigits } from '../../lib/jalali';

const MARKS: MarkType[] = ['important', 'review', 'hard', 'mistake', 'tip'];
const ERROR_TYPES = ['unknown', 'forgotten', 'careless', 'time'] as const;

interface DraftItem {
  question_id: string;
  result: TestResult;
  duration_seconds: number | null;
  marks: MarkType[];
  error_type: string | null;
}

export default function TestsPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'record' | 'import' | 'notebook'>('record');
  const [selectedResource, setSelectedResource] = useState('');
  const [draft, setDraft] = useState<Record<string, DraftItem>>({});
  const [showImport, setShowImport] = useState(false);
  const importTextRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: resources } = useQuery({
    queryKey: ['resources'],
    queryFn: () => get<Resource[]>('/resources', { type: 'book_test' }),
  });

  const { data: questions, isLoading: loadingQuestions } = useQuery({
    queryKey: ['questions', selectedResource],
    queryFn: () => get<Question[]>(`/resources/${selectedResource}/questions`, { page_size: 100 }),
    enabled: !!selectedResource,
  });

  const { data: records } = useQuery({
    queryKey: ['test-records'],
    queryFn: () => get<TestRecord[]>('/test-records', { page_size: 30 }),
    enabled: tab === 'notebook',
  });

  const importBook = useMutation({
    mutationFn: async (payload: { text?: string; file?: File }) => {
      let body: unknown;
      if (payload.text) {
        body = JSON.parse(payload.text);
      } else if (payload.file) {
        const text = await payload.file.text();
        body = JSON.parse(text);
      }
      // اگر قبلاً وارد شده، با تأیید کاربر به‌روزرسانی می‌کنیم
      return post('/resources/import-book', body);
    },
    onSuccess: (r) => {
      const d = r.data as { questions: number; title: string; updated: boolean };
      toast.show(`کتاب «${d.title}» ${d.updated ? 'به‌روزرسانی' : 'وارد'} شد — ${toFaDigits(d.questions)} سوال ✅`);
      setShowImport(false);
      if (importTextRef.current) importTextRef.current.value = '';
      void queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
    onError: (e) => {
      const msg = errorMessage(e);
      const isDuplicate = axiosIsDuplicate(e);
      if (isDuplicate) {
        if (confirm(msg + '\n\nآیا می‌خواهی کتاب را به‌روزرسانی کنی؟')) {
          retryImportAsUpdate();
          return;
        }
      }
      toast.show(msg, 'error');
    },
  });

  const retryImportAsUpdate = async () => {
    const payload = getPendingImport();
    if (!payload) return;
    try {
      let body: unknown;
      if (payload.text) body = JSON.parse(payload.text);
      else if (payload.file) body = JSON.parse(await payload.file.text());
      const r = await post('/resources/import-book', body, { update_existing: true });
      const d = r.data as { questions: number; title: string };
      toast.show(`کتاب «${d.title}» به‌روزرسانی شد — ${toFaDigits(d.questions)} سوال ✅`);
      setShowImport(false);
      void queryClient.invalidateQueries({ queryKey: ['resources'] });
    } catch (err) {
      toast.show(errorMessage(err), 'error');
    }
  };

  const submitRecords = useMutation({
    mutationFn: () => {
      const recordsList = Object.values(draft);
      return post('/test-records', { records: recordsList });
    },
    onSuccess: (_, __) => {
      toast.show(`${toFaDigits(Object.keys(draft).length)} تست ثبت شد ✅`);
      setDraft({});
      void queryClient.invalidateQueries({ queryKey: ['test-records'] });
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      void queryClient.invalidateQueries({ queryKey: ['overview-7d'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const setDraftItem = (qid: string, patch: Partial<DraftItem>) => {
    setDraft((prev) => ({
      ...prev,
      [qid]: {
        question_id: qid, result: prev[qid]?.result ?? 'correct',
        duration_seconds: prev[qid]?.duration_seconds ?? null,
        marks: prev[qid]?.marks ?? [], error_type: prev[qid]?.error_type ?? null,
        ...patch,
      },
    }));
  };

  const toggleMark = (qid: string, mark: MarkType) => {
    const current = draft[qid]?.marks ?? [];
    setDraftItem(qid, {
      marks: current.includes(mark) ? current.filter((m) => m !== mark) : [...current, mark],
    });
  };

  const draftCount = Object.keys(draft).length;

  return (
    <div>
      <PageHeader
        title="تست‌ها"
        subtitle="ثبت سریع نتایج، علامت‌گذاری و دفترچه خطا"
        actions={<button className="btn-primary" onClick={() => setShowImport(true)}>📖 وارد کردن کتاب</button>}
      />

      <div className="flex gap-2 mb-5 bg-slate-100 rounded-xl p-1 w-fit">
        {([
          ['record', 'ثبت تست'],
          ['notebook', 'دفترچه خطا'],
        ] as const).map(([key, label]) => (
          <button key={key}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${tab === key ? 'bg-white shadow text-primary-700' : 'text-slate-500'}`}
            onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'record' && (
        <>
          <div className="card mb-4 !py-3">
            <label className="label">انتخاب کتاب تست</label>
            <select className="input" value={selectedResource}
                    onChange={(e) => { setSelectedResource(e.target.value); setDraft({}); }}>
              <option value="">— یک کتاب انتخاب کن —</option>
              {(resources?.data ?? []).map((r) => (
                <option key={r.id} value={r.id}>{r.title} {r.publisher ? `(${r.publisher})` : ''}</option>
              ))}
            </select>
          </div>

          {!selectedResource ? (
            <EmptyState icon="📖" title="کتابی انتخاب نشده"
              description="برای ثبت تست، اول یک کتاب تست انتخاب کن. اگر کتابی نداری، آن را وارد کن."
              action={<button className="btn-primary text-xs" onClick={() => setShowImport(true)}>وارد کردن کتاب JSON</button>} />
          ) : loadingQuestions ? (
            <Spinner />
          ) : (
            <>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-slate-500">
                  نتیجه هر سوال را مشخص کن؛ امکان ثبت دسته‌ای و علامت‌گذاری هست.
                </p>
                {draftCount > 0 && (
                  <button className="btn-success" disabled={submitRecords.isPending}
                          onClick={() => submitRecords.mutate()}>
                    ثبت {toFaDigits(draftCount)} تست
                  </button>
                )}
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {(questions?.data ?? []).map((q) => {
                  const item = draft[q.id];
                  return (
                    <div key={q.id} className={`card !p-4 ${item ? 'border-primary-300 bg-primary-50/30' : ''}`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-bold text-primary-700">سوال {toFaDigits(q.number)}</span>
                        <span className="chip bg-slate-100 text-slate-600">{q.topic_title}</span>
                        {q.difficulty && (
                          <span className={`chip ${
                            q.difficulty === 'easy' ? 'bg-emerald-100 text-emerald-700'
                            : q.difficulty === 'medium' ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'}`}>
                            {DIFFICULTY_LABELS[q.difficulty]}
                          </span>
                        )}
                      </div>
                      {q.text && <p className="text-xs text-slate-500 mb-2">{q.text}</p>}
                      <div className="flex gap-1.5 mb-2">
                        {(['correct', 'wrong', 'blank'] as TestResult[]).map((res) => (
                          <button key={res}
                            className={`btn !py-1 !px-3 text-xs flex-1 ${
                              item?.result === res
                                ? res === 'correct' ? 'bg-emerald-600 text-white'
                                : res === 'wrong' ? 'bg-red-600 text-white'
                                : 'bg-slate-600 text-white'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                            onClick={() => setDraftItem(q.id, {
                              result: res,
                              error_type: res === 'wrong' ? (item?.error_type ?? 'unknown') : null,
                            })}>
                            {res === 'correct' ? '✓ درست' : res === 'wrong' ? '✗ غلط' : '— نزده'}
                          </button>
                        ))}
                      </div>
                      {/* تیک‌ها — یک سوال می‌تواند چند تیک همزمان داشته باشد */}
                      <div className="flex flex-wrap gap-1">
                        {MARKS.map((mark) => (
                          <button key={mark}
                            className={`chip border cursor-pointer ${
                              item?.marks.includes(mark) ? MARK_COLORS[mark] : 'bg-white text-slate-400 border-slate-200'
                            }`}
                            onClick={() => toggleMark(q.id, mark)}>
                            {MARK_LABELS[mark]}
                          </button>
                        ))}
                      </div>
                      {/* نوع اشتباه — فقط برای غلط */}
                      {item?.result === 'wrong' && (
                        <div className="mt-2 flex flex-wrap gap-1 items-center">
                          <span className="text-[11px] text-slate-400">نوع اشتباه:</span>
                          {ERROR_TYPES.map((et) => (
                            <button key={et}
                              className={`chip border cursor-pointer ${
                                item.error_type === et ? 'bg-red-600 text-white border-red-600' : 'bg-white text-slate-500 border-slate-200'
                              }`}
                              onClick={() => setDraftItem(q.id, { error_type: et })}>
                              {ERROR_TYPE_LABELS[et]}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              {draftCount > 0 && (
                <button className="btn-success w-full mt-4" disabled={submitRecords.isPending}
                        onClick={() => submitRecords.mutate()}>
                  ثبت نهایی {toFaDigits(draftCount)} تست
                </button>
              )}
            </>
          )}
        </>
      )}

      {tab === 'notebook' && (
        (records?.data ?? []).length === 0 ? (
          <EmptyState icon="📔" title="دفترچه خطا خالی است"
            description="وقتی تستی را غلط بزنی، اینجا با نوع اشتباه ثبت می‌شود تا برای مرور برنامه‌ریزی کنی." />
        ) : (
          <div className="card !p-0 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-right px-4 py-3">سوال</th>
                  <th className="text-right px-4 py-3">مبحث</th>
                  <th className="text-right px-4 py-3">نتیجه</th>
                  <th className="text-right px-4 py-3">نوع اشتباه</th>
                  <th className="text-right px-4 py-3">تاریخ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(records?.data ?? []).map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60">
                    <td className="px-4 py-3 font-medium">{r.question_number ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{r.topic_title ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`chip ${
                        r.result === 'correct' ? 'bg-emerald-100 text-emerald-700'
                        : r.result === 'wrong' ? 'bg-red-100 text-red-700'
                        : 'bg-slate-100 text-slate-600'}`}>
                        {r.result === 'correct' ? 'درست' : r.result === 'wrong' ? 'غلط' : 'نزده'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {r.error_type ? ERROR_TYPE_LABELS[r.error_type] : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">{formatJalali(r.solved_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {/* مودال وارد کردن کتاب */}
      <Modal open={showImport} onClose={() => setShowImport(false)} title="وارد کردن کتاب تست (JSON)" wide>
        <div className="space-y-4">
          <p className="text-sm text-slate-500 leading-relaxed">
            فایل JSON کتاب را انتخاب کن یا محتوای آن را بچسبان. ساختار استاندارد:
            <code className="block mt-2 bg-slate-50 rounded-lg p-3 text-xs leading-relaxed overflow-x-auto" dir="ltr">{`{
  "title": "نام کتاب", "publisher": "ناشر", "subject": "حسابان",
  "chapters": [{ "title": "فصل ۱", "topics": [
    { "title": "مبحث ۱", "questions": [
      { "number": "1", "answer": "2", "difficulty": "easy", "importance": 2 }
    ]}
  ]}]
}`}</code>
          </p>
          <input type="file" accept=".json,application/json" className="input"
                 onChange={(e) => {
                   const f = e.target.files?.[0];
                   if (f) {
                     storePendingImport({ file: f });
                     importBook.mutate({ file: f });
                   }
                 }} />
          <div className="text-center text-xs text-slate-400">یا</div>
          <textarea ref={importTextRef} className="input font-mono" rows={8} dir="ltr"
                    placeholder='{ "title": "..." }'
                    onChange={(e) => storePendingImport({ text: e.target.value })} />
          <button className="btn-primary w-full" disabled={importBook.isPending}
                  onClick={() => {
                    const text = importTextRef.current?.value.trim();
                    if (!text) { toast.show('فایل یا متن JSON را وارد کن.', 'error'); return; }
                    storePendingImport({ text });
                    importBook.mutate({ text });
                  }}>
            {importBook.isPending ? 'در حال وارد کردن...' : 'وارد کردن کتاب'}
          </button>
          <button
            className="btn-secondary w-full text-xs"
            onClick={() => {
              const sample = {
                title: 'کتاب نمونه — حد و مشتق', publisher: 'نشر نمونه', subject: 'حسابان',
                chapters: [{
                  title: 'فصل تابع',
                  topics: [{
                    title: 'تعریف تابع',
                    questions: [
                      { number: '1', answer: '1', difficulty: 'easy', importance: 2 },
                      { number: '2', answer: '3', difficulty: 'medium' },
                      { number: '3', answer: '2', difficulty: 'hard', tags: ['تابع'] },
                    ],
                  }],
                }],
              };
              if (importTextRef.current) {
                importTextRef.current.value = JSON.stringify(sample, null, 2);
                storePendingImport({ text: importTextRef.current.value });
              }
            }}>
            پر کردن با نمونه
          </button>
        </div>
      </Modal>
    </div>
  );
}

// نگهداری موقت محتوای import برای حالت «به‌روزرسانی»
let pendingImport: { text?: string; file?: File } | null = null;
function storePendingImport(p: { text?: string; file?: File }) {
  pendingImport = p;
}
function getPendingImport() {
  return pendingImport;
}
function axiosIsDuplicate(e: unknown): boolean {
  return (
    typeof e === 'object' && e !== null &&
    'response' in e &&
    ((e as { response?: { data?: { error?: { details?: { duplicate?: boolean } } } } })
      .response?.data?.error?.details?.duplicate === true)
  );
}

// برای نمایش شمارش سوالات صفحه PercentBar بی‌استفاده است اما import تمیز بماند
void PercentBar;
void faNumber;
void api;
