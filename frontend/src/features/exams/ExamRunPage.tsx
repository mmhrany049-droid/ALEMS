// اجرای آزمون — تایمر، ثبت پاسخ‌ها و کارنامه با تحلیل سختی
import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { errorMessage, get, post } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, PageHeader, Spinner, StatCard } from '../../components/ui';
import {
  DIFFICULTY_LABELS, type DifficultyStat, type Exam, type ExamResult, type Question, type TestResult,
} from '../../types';
import { faNumber, faPercent, toFaDigits } from '../../lib/jalali';

const RESULT_BUTTONS: { value: TestResult; label: string; active: string }[] = [
  { value: 'correct', label: '✓ درست', active: 'bg-emerald-600 text-white' },
  { value: 'wrong', label: '✗ غلط', active: 'bg-red-600 text-white' },
  { value: 'blank', label: '— نزده', active: 'bg-slate-500 text-white' },
];

export default function ExamRunPage() {
  const { examId } = useParams<{ examId: string }>();
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<string, TestResult>>({});
  const [remaining, setRemaining] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const { data: examData, isLoading } = useQuery({
    queryKey: ['exam', examId],
    queryFn: () => get<Exam>(`/exams/${examId}`),
    enabled: !!examId,
  });

  const { data: resultData } = useQuery({
    queryKey: ['exam-result', examId],
    queryFn: () => get<{
      exam: Exam;
      result: ExamResult & { finished_at: string };
      by_subject: { subject: string; total: number; correct: number; wrong: number; blank: number;
        percent_konkur: number | null; percent_no_penalty: number | null }[];
    }>(`/exams/${examId}/result`),
    enabled: !!examId && examData?.data?.status === 'finished',
  });

  // سوالات آزمون: از همان منبع کتاب می‌گیریم چون endpoint اختصاصی سوالات آزمون نداریم —
  // از exam detail فقط تعداد را داریم؛ پاسخ‌ها بر اساس سوالات داده‌شده ثبت می‌شوند.
  const { data: examQuestions } = useQuery({
    queryKey: ['exam-questions', examId],
    queryFn: async (): Promise<Question[]> => {
      if (!examId || examData?.data?.status === 'finished') return [] as Question[];
      try {
        const r = await get<Question[]>(`/exams/${examId}/questions`);
        return r.data;
      } catch {
        return [] as Question[];
      }
    },
    enabled: !!examId,
  });

  const start = useMutation({
    mutationFn: () => post(`/exams/${examId}/start`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['exam', examId] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const submit = useMutation({
    mutationFn: () => {
      const payload = Object.entries(answers).map(([question_id, result]) => ({
        question_id, result,
      }));
      return post(`/exams/${examId}/submit`, { answers: payload });
    },
    onSuccess: () => {
      toast.show('پاسخ‌ها ثبت و نمره‌دهی شد 🎉');
      setSubmitted(true);
      void queryClient.invalidateQueries({ queryKey: ['exam', examId] });
      void queryClient.invalidateQueries({ queryKey: ['exam-result', examId] });
      void queryClient.invalidateQueries({ queryKey: ['exams'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  // تایمر آزمون
  const exam = examData?.data;
  useEffect(() => {
    if (exam?.status === 'in_progress' && remaining === null) {
      const startedAt = exam.started_at ? new Date(exam.started_at).getTime() : Date.now();
      const endAt = startedAt + exam.duration_minutes * 60000;
      const tick = () => {
        const left = Math.max(0, Math.floor((endAt - Date.now()) / 1000));
        setRemaining(left);
        if (left === 0 && !submitted) {
          // پایان زمان — ثبت خودکار
          toast.show('زمان آزمون تمام شد — پاسخ‌ها ثبت می‌شود', 'info');
          submit.mutate();
        }
      };
      tick();
      const timer = setInterval(tick, 1000);
      return () => clearInterval(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exam?.status, exam?.started_at]);

  const questions = examQuestions ?? [];
  const answeredCount = Object.keys(answers).length;

  const timeText = useMemo(() => {
    if (remaining === null) return '—';
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    return `${toFaDigits(String(m).padStart(2, '0'))}:${toFaDigits(String(s).padStart(2, '0'))}`;
  }, [remaining]);

  if (isLoading) return <Spinner />;

  if (!exam) {
    return <EmptyState icon="🤔" title="آزمون یافت نشد" action={<Link className="btn-primary text-xs" to="/exams">بازگشت به آزمون‌ها</Link>} />;
  }

  // ---------- کارنامه ----------
  if (exam.status === 'finished' && resultData?.data) {
    const r = resultData.data.result;
    const breakdown = Object.entries(r.difficulty_breakdown) as [string, DifficultyStat][];
    return (
      <div>
        <PageHeader
          title={`کارنامه — ${resultData.data.exam.title}`}
          subtitle="نتیجه با فرمول کنکوری محاسبه شده است"
          actions={<Link to="/exams" className="btn-secondary text-xs">بازگشت</Link>}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard label="درصد کنکوری" value={<span className={r.percent_konkur !== null && r.percent_konkur < 0 ? 'text-red-600' : 'text-emerald-600'}>{faPercent(r.percent_konkur)}</span>} hint="(درست − ۰.۳۳ × غلط) ÷ کل" accent="bg-primary-600" />
          <StatCard label="درصد بدون غلط" value={faPercent(r.percent_no_penalty)} hint="درست ÷ کل" accent="bg-blue-500" />
          <StatCard label="درست" value={faNumber(r.correct_count)} accent="bg-emerald-500" />
          <StatCard label="غلط / نزده" value={`${faNumber(r.wrong_count)} / ${faNumber(r.blank_count)}`} accent="bg-red-500" />
        </div>

        <h2 className="font-bold text-slate-900 mb-3">تحلیل بر اساس سختی (AT-22)</h2>
        <div className="grid gap-3 md:grid-cols-3 mb-6">
          {breakdown.map(([key, stat]) => (
            <div key={key} className="card !p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-700 text-sm">{DIFFICULTY_LABELS[key] ?? key}</span>
                <span className="text-xs text-slate-400">{faNumber(stat.total)} سوال</span>
              </div>
              <div className="text-2xl font-bold text-slate-900 mb-1">{faPercent(stat.percent_konkur)}</div>
              <div className="text-xs text-slate-400">
                درست {faNumber(stat.correct)} · غلط {faNumber(stat.wrong)} · نزده {faNumber(stat.blank)}
              </div>
            </div>
          ))}
        </div>

        <h2 className="font-bold text-slate-900 mb-3">به تفکیک درس</h2>
        {resultData.data.by_subject.length === 0 ? (
          <p className="text-sm text-slate-400">اطلاعاتی نیست.</p>
        ) : (
          <div className="card !p-0 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-right px-4 py-3">درس</th>
                  <th className="text-right px-4 py-3">کل</th>
                  <th className="text-right px-4 py-3">درست</th>
                  <th className="text-right px-4 py-3">غلط</th>
                  <th className="text-right px-4 py-3">نزده</th>
                  <th className="text-right px-4 py-3">درصد کنکوری</th>
                  <th className="text-right px-4 py-3">بدون غلط</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {resultData.data.by_subject.map((s) => (
                  <tr key={s.subject}>
                    <td className="px-4 py-3 font-medium">{s.subject}</td>
                    <td className="px-4 py-3">{faNumber(s.total)}</td>
                    <td className="px-4 py-3 text-emerald-600">{faNumber(s.correct)}</td>
                    <td className="px-4 py-3 text-red-600">{faNumber(s.wrong)}</td>
                    <td className="px-4 py-3 text-slate-500">{faNumber(s.blank)}</td>
                    <td className="px-4 py-3 font-bold">{faPercent(s.percent_konkur)}</td>
                    <td className="px-4 py-3">{faPercent(s.percent_no_penalty)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  // ---------- قبل از شروع ----------
  if (exam.status === 'planned') {
    return (
      <div>
        <PageHeader title={exam.title} subtitle="شرایط آزمون را آماده کن" actions={<Link to="/exams" className="btn-secondary text-xs">بازگشت</Link>} />
        <div className="card max-w-lg mx-auto text-center">
          <div className="text-5xl mb-4">🎯</div>
          <h2 className="font-bold text-lg text-slate-900 mb-2">{exam.title}</h2>
          <p className="text-sm text-slate-500 mb-1">
            {toFaDigits(exam.question_count ?? 0)} سوال · {toFaDigits(exam.duration_minutes)} دقیقه
          </p>
          <p className="text-xs text-slate-400 mb-6 leading-relaxed">
            تایمر با شروع آزمون فعال می‌شود. سوالات بی‌پاسخ «نزده» ثبت می‌شوند.
          </p>
          <button className="btn-primary w-full !py-3" disabled={start.isPending}
                  onClick={() => start.mutate()}>
            شروع آزمون
          </button>
        </div>
      </div>
    );
  }

  // ---------- در حال برگزاری ----------
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{exam.title}</h1>
          <p className="text-sm text-slate-500">
            پاسخ داده: {faNumber(answeredCount)} از {faNumber(questions.length)}
          </p>
        </div>
        <div className={`text-2xl font-bold tabular-nums px-4 py-2 rounded-xl ${
          remaining !== null && remaining < 300 ? 'bg-red-50 text-red-600 animate-pulse' : 'bg-slate-100 text-slate-700'
        }`} dir="ltr">
          ⏱ {timeText}
        </div>
      </div>

      {questions.length === 0 ? (
        <EmptyState icon="⏳" title="سوالات آزمون بارگذاری نشد" />
      ) : (
        <>
          <div className="grid gap-3 md:grid-cols-2">
            {questions.map((q, i) => (
              <div key={q.id} className={`card !p-4 ${answers[q.id] ? 'border-primary-300 bg-primary-50/30' : ''}`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="size-7 rounded-lg bg-primary-600 text-white grid place-items-center text-xs font-bold">
                    {toFaDigits(i + 1)}
                  </span>
                  <span className="chip bg-slate-100 text-slate-600">{q.topic_title}</span>
                </div>
                {q.text && <p className="text-xs text-slate-500 mb-2">{q.text}</p>}
                <div className="flex gap-1.5">
                  {RESULT_BUTTONS.map((btn) => (
                    <button key={btn.value}
                      className={`btn !py-1 !px-3 text-xs flex-1 ${
                        answers[q.id] === btn.value ? btn.active : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                      onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: btn.value }))}>
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button
            className="btn-success w-full mt-5 !py-3"
            disabled={submit.isPending || submitted}
            onClick={() => {
              if (confirm(`ثبت نهایی آزمون؟ ${faNumber(questions.length - answeredCount)} سوال بدون پاسخ نزده ثبت می‌شود.`)) {
                submit.mutate();
              }
            }}>
            ثبت نهایی و مشاهده نتیجه
          </button>
        </>
      )}
    </div>
  );
}
