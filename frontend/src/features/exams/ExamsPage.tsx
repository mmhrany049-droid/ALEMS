// صفحه آزمون — لیست، ساخت آزمون، ورود به جلسه
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { errorMessage, get, post } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, Modal, PageHeader, Spinner } from '../../components/ui';
import { DIFFICULTY_LABELS, type Exam, type Question, type Resource } from '../../types';
import { faNumber, faPercent, formatJalali, toFaDigits } from '../../lib/jalali';

export default function ExamsPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    title: '',
    exam_type: 'mock' as 'mock' | 'subject',
    duration_minutes: 60,
    resource_id: '',
    count: 10,
  });
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);

  const { data: exams, isLoading } = useQuery({
    queryKey: ['exams'],
    queryFn: () => get<Exam[]>('/exams', { page_size: 30 }),
  });
  const { data: resources } = useQuery({
    queryKey: ['resources'],
    queryFn: () => get<Resource[]>('/resources', { type: 'book_test' }),
  });

  const { data: poolQuestions } = useQuery({
    queryKey: ['exam-pool', form.resource_id],
    queryFn: () => get<Question[]>(`/resources/${form.resource_id}/questions`, { page_size: 200 }),
    enabled: !!form.resource_id && showCreate,
  });

  const createExam = useMutation({
    mutationFn: () =>
      post<Exam>('/exams', {
        title: form.title,
        exam_type: form.exam_type,
        duration_minutes: form.duration_minutes,
        question_ids: selectedQuestions,
      }),
    onSuccess: (r) => {
      toast.show('آزمون ساخته شد. موفق باشی! 🎯');
      setShowCreate(false);
      setSelectedQuestions([]);
      void queryClient.invalidateQueries({ queryKey: ['exams'] });
      navigate(`/exams/${r.data.id}/run`);
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const pool = poolQuestions?.data ?? [];

  const quickSelect = () => {
    // انتخاب تصادفی N سوال برای شبیه‌سازی آزمون
    const shuffled = [...pool].sort(() => Math.random() - 0.5);
    setSelectedQuestions(shuffled.slice(0, form.count).map((q) => q.id));
  };

  return (
    <div>
      <PageHeader
        title="آزمون"
        subtitle="آزمون آزمایشی (چند درس) یا امتحان (یک درس) با تایمر و نمره‌دهی کنکوری"
        actions={<button className="btn-primary" onClick={() => setShowCreate(true)}>+ آزمون جدید</button>}
      />

      {isLoading ? (
        <Spinner />
      ) : (exams?.data ?? []).length === 0 ? (
        <EmptyState
          icon="🎯"
          title="هنوز آزمونی نساخته‌ای"
          description="با سوالات کتاب‌هایت آزمون بساز؛ درصد کنکوری و تحلیل سختی به‌صورت خودکار محاسبه می‌شود."
          action={<button className="btn-primary text-xs" onClick={() => setShowCreate(true)}>ساخت اولین آزمون</button>}
        />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {(exams?.data ?? []).map((exam) => (
            <div key={exam.id} className="card !p-4">
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <div className="font-bold text-slate-900 text-sm">{exam.title}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    {exam.exam_type === 'mock' ? 'آزمون آزمایشی' : 'امتحان'} ·{' '}
                    {toFaDigits(exam.duration_minutes)} دقیقه ·{' '}
                    {toFaDigits(exam.question_count ?? 0)} سوال · {formatJalali(exam.scheduled_at)}
                  </div>
                </div>
                <span className={`chip ${
                  exam.status === 'finished' ? 'bg-slate-100 text-slate-600'
                  : exam.status === 'in_progress' ? 'bg-amber-100 text-amber-700'
                  : 'bg-blue-100 text-blue-700'}`}>
                  {exam.status === 'finished' ? 'تمام شده' : exam.status === 'in_progress' ? 'در حال برگزاری' : 'آماده'}
                </span>
              </div>
              {exam.status === 'finished' && exam.percent_konkur != null && (
                <div className="text-sm text-slate-600 mb-2">
                  درصد کنکوری: <strong className={exam.percent_konkur < 0 ? 'text-red-600' : 'text-emerald-600'}>
                    {faPercent(exam.percent_konkur)}
                  </strong>
                  {' · '}بدون غلط: {faPercent(exam.percent_no_penalty ?? null)}
                </div>
              )}
              <div className="flex gap-2">
                {exam.status !== 'finished' ? (
                  <Link to={`/exams/${exam.id}/run`} className="btn-primary !py-1.5 text-xs">
                    {exam.status === 'in_progress' ? 'ادامه آزمون' : 'شروع آزمون'}
                  </Link>
                ) : (
                  <Link to={`/exams/${exam.id}/run`} className="btn-secondary !py-1.5 text-xs">
                    مشاهده کارنامه
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ساخت آزمون */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="آزمون جدید" wide>
        <div className="space-y-4">
          <div>
            <label className="label">عنوان آزمون</label>
            <input className="input" value={form.title}
                   onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                   placeholder="مثلاً: آزمون آزمایشی حسابان" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">نوع</label>
              <select className="input" value={form.exam_type}
                      onChange={(e) => setForm((f) => ({ ...f, exam_type: e.target.value as 'mock' | 'subject' }))}>
                <option value="mock">آزمون آزمایشی</option>
                <option value="subject">امتحان (یک درس)</option>
              </select>
            </div>
            <div>
              <label className="label">مدت (دقیقه)</label>
              <input type="number" className="input" dir="ltr" min={5} max={480}
                     value={form.duration_minutes}
                     onChange={(e) => setForm((f) => ({ ...f, duration_minutes: Number(e.target.value) }))} />
            </div>
          </div>
          <div>
            <label className="label">از کتاب</label>
            <select className="input" value={form.resource_id}
                    onChange={(e) => { setForm((f) => ({ ...f, resource_id: e.target.value })); setSelectedQuestions([]); }}>
              <option value="">— انتخاب کن —</option>
              {(resources?.data ?? []).map((r) => (
                <option key={r.id} value={r.id}>{r.title}</option>
              ))}
            </select>
          </div>

          {form.resource_id && (
            <>
              <div className="flex items-center gap-2">
                <button className="btn-secondary !py-1.5 text-xs"
                        onClick={quickSelect}
                        disabled={pool.length === 0}>
                  🎲 انتخاب تصادفی {toFaDigits(form.count)} سوال
                </button>
                <input type="number" className="input !w-20 !py-1.5 text-xs" dir="ltr" min={1} max={200}
                       value={form.count}
                       onChange={(e) => setForm((f) => ({ ...f, count: Number(e.target.value) }))} />
                <button className="btn-secondary !py-1.5 text-xs"
                        onClick={() => setSelectedQuestions(pool.map((q) => q.id))}>
                  انتخاب همه ({toFaDigits(pool.length)})
                </button>
                {selectedQuestions.length > 0 && (
                  <button className="btn-secondary !py-1.5 text-xs"
                          onClick={() => setSelectedQuestions([])}>
                    پاک کردن انتخاب‌ها
                  </button>
                )}
              </div>
              <div className="border border-slate-200 rounded-xl max-h-72 overflow-y-auto divide-y divide-slate-100">
                {pool.map((q) => {
                  const checked = selectedQuestions.includes(q.id);
                  return (
                    <label key={q.id} className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50 cursor-pointer">
                      <input type="checkbox" checked={checked}
                             onChange={() => setSelectedQuestions((prev) =>
                               checked ? prev.filter((id) => id !== q.id) : [...prev, q.id])} />
                      <span className="text-xs font-bold text-primary-700">{toFaDigits(q.number)}</span>
                      <span className="text-xs text-slate-500 flex-1">{q.topic_title}</span>
                      {q.difficulty && <span className="chip bg-slate-100 text-slate-600 !text-[10px]">{DIFFICULTY_LABELS[q.difficulty]}</span>}
                    </label>
                  );
                })}
              </div>
            </>
          )}

          <button className="btn-primary w-full"
                  disabled={createExam.isPending || !form.title.trim() || selectedQuestions.length === 0}
                  onClick={() => createExam.mutate()}>
            ساخت آزمون با {faNumber(selectedQuestions.length)} سوال
          </button>
        </div>
      </Modal>
    </div>
  );
}
