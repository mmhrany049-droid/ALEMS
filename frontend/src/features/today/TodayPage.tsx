// Today Hub — «امروز چه کارهایی باید انجام دهم؟» (۷.۲)
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { errorMessage, get, post } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, PageHeader, StatCard } from '../../components/ui';
import { useAuth } from '../../hooks/useAuth';
import {
  ACTIVITY_TYPE_LABELS, type Activity, type Plan, type ReviewItem, type StudentState,
} from '../../types';
import { faNumber, faPercent, formatJalaliLong, timeAgo, todayISO, toFaDigits } from '../../lib/jalali';

const MOODS = ['عالی', 'خوب', 'معمولی', 'خسته', 'کمی آشفته'];
const CONDITIONS = ['متمرکز', 'سرحال', 'خسته', 'پراکنده', 'آرام'];

export default function TodayPage() {
  const { profile } = useAuth();
  const today = todayISO();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [checkin, setCheckin] = useState({ energy_level: 3, mood: '', study_condition: '' });

  const { data: state } = useQuery({
    queryKey: ['state', today],
    queryFn: () => get<StudentState[]>('/students/me/state', { from: today, to: today }),
  });
  const { data: plan } = useQuery({
    queryKey: ['plan', today],
    queryFn: () => get<Plan | null>(`/plans`, { date: today }),
  });
  const { data: reviews } = useQuery({
    queryKey: ['review-queue'],
    queryFn: () => get<ReviewItem[]>('/reviews/queue'),
  });
  const { data: overview } = useQuery({
    queryKey: ['overview-7d'],
    queryFn: () => {
      const from = new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10);
      return get<OverviewData>('/analytics/overview', { from, to: today });
    },
  });
  const { data: activities } = useQuery({
    queryKey: ['today-activities'],
    queryFn: () => get<Activity[]>('/activities', { from: today, to: today, page_size: 10 }),
  });
  const { data: exams } = useQuery({
    queryKey: ['upcoming-exams'],
    queryFn: () => get<ExamLite[]>('/exams', { status: 'planned', page_size: 5 }),
  });

  const checkinMutation = useMutation({
    mutationFn: () =>
      post('/students/me/state', {
        date: today,
        energy_level: checkin.energy_level,
        mood: checkin.mood || undefined,
        study_condition: checkin.study_condition || undefined,
      }),
    onSuccess: () => {
      toast.show('وضعیت امروز ثبت شد. موفق باشی! 💪');
      void queryClient.invalidateQueries({ queryKey: ['state', today] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const postponeReview = useMutation({
    mutationFn: (id: string) => post(`/reviews/${id}/postpone`, { days: 1 }),
    onSuccess: () => {
      toast.show('مرور برای فردا به‌عقب افتاد ⏭');
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const completeReview = useMutation({
    mutationFn: (id: string) => post(`/reviews/${id}/complete`),
    onSuccess: () => {
      toast.show('مرور شد! آفرین ✅');
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const todayState = state?.data?.[0];
  const pendingReviews = (reviews?.data ?? []).filter((r) => r.status === 'pending');
  const planItems = plan?.data?.items ?? [];
  const recentActivities = activities?.data ?? [];

  return (
    <div>
      <PageHeader
        title={`سلام ${profile?.full_name ?? ''} 👋`}
        subtitle={`امروز ${formatJalaliLong(today)} — برنامه‌ات را شروع کن`}
      />

      <div className="grid gap-5 lg:grid-cols-3">
        {/* Daily Check-in */}
        <div className="card">
          <h2 className="font-bold text-slate-900 mb-3">وضعیت امروزت چطوره؟</h2>
          {todayState ? (
            <div className="space-y-2 text-sm text-slate-600">
              <p>انرژی امروز: <strong>{toFaDigits(todayState.energy_level)} از ۵</strong></p>
              {todayState.mood && <p>حال روحی: {todayState.mood}</p>}
              {todayState.study_condition && <p>شرایط مطالعه: {todayState.study_condition}</p>}
              <button
                className="btn-secondary !py-1.5 text-xs"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['state', today] })}
              >
                ویرایش
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="label">سطح انرژی: {toFaDigits(checkin.energy_level)} از ۵</label>
                <input
                  type="range" min={1} max={5} step={1} dir="ltr"
                  value={checkin.energy_level}
                  onChange={(e) => setCheckin((c) => ({ ...c, energy_level: Number(e.target.value) }))}
                  className="w-full accent-primary-600"
                />
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>بی‌انرژی</span><span>پرانرژی</span>
                </div>
              </div>
              <div>
                <label className="label">حال روحی (اختیاری)</label>
                <div className="flex flex-wrap gap-1.5">
                  {MOODS.map((m) => (
                    <button key={m}
                      className={`chip border cursor-pointer ${checkin.mood === m ? 'bg-primary-600 text-white border-primary-600' : 'bg-slate-50 text-slate-600 border-slate-200'}`}
                      onClick={() => setCheckin((c) => ({ ...c, mood: c.mood === m ? '' : m }))}>
                      {m}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="label">شرایط مطالعه (اختیاری)</label>
                <div className="flex flex-wrap gap-1.5">
                  {CONDITIONS.map((c) => (
                    <button key={c}
                      className={`chip border cursor-pointer ${checkin.study_condition === c ? 'bg-primary-600 text-white border-primary-600' : 'bg-slate-50 text-slate-600 border-slate-200'}`}
                      onClick={() => setCheckin((x) => ({ ...x, study_condition: x.study_condition === c ? '' : c }))}>
                      {c}
                    </button>
                  ))}
                </div>
              </div>
              <button
                className="btn-primary w-full"
                disabled={checkinMutation.isPending}
                onClick={() => checkinMutation.mutate()}
              >
                ثبت وضعیت امروز
              </button>
            </div>
          )}
        </div>

        {/* برنامه امروز */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-slate-900">برنامه امروز</h2>
            <Link to="/planning" className="text-xs text-primary-600 hover:underline">مدیریت برنامه ←</Link>
          </div>
          {planItems.length === 0 ? (
            <EmptyState
              icon="🗓"
              title="برنامه‌ای برای امروز ثبت نشده"
              description="از بخش «برنامه» می‌توانی برنامه هفتگی بسازی یا برنامه امروز را دستی وارد کنی."
              action={<Link to="/planning" className="btn-primary text-xs">ساخت برنامه</Link>}
            />
          ) : (
            <div className="space-y-2">
              {planItems.map((item, i) => (
                <div key={i} className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2">
                  <span className="text-xs font-bold text-primary-700 tabular-nums" dir="ltr">
                    {toFaDigits(item.start)} – {toFaDigits(item.end)}
                  </span>
                  <span className="flex-1 text-sm text-slate-700">{item.title}</span>
                  {item.subject && <span className="chip bg-primary-50 text-primary-700">{item.subject}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* صف مرور ضروری */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-slate-900">
              مرورهای امروز
              {pendingReviews.length > 0 && (
                <span className="mr-2 chip bg-red-100 text-red-700">{toFaDigits(pendingReviews.length)} مورد</span>
              )}
            </h2>
            <Link to="/review" className="text-xs text-primary-600 hover:underline">همه مرورها ←</Link>
          </div>
          {pendingReviews.length === 0 ? (
            <EmptyState icon="🎉" title="صف مرور خالی است" description="الان چیزی برای مرور نداری. به همین زودی برنگرد! تست بزن تا غلط‌هات اینجا جمع شوند." />
          ) : (
            <div className="space-y-2">
              {pendingReviews.slice(0, 5).map((item) => (
                <div key={item.id} className="flex items-center gap-3 rounded-xl border border-slate-100 px-3 py-2">
                  <span className="chip bg-slate-100 text-slate-600">اولویت {toFaDigits(item.priority)}</span>
                  <div className="flex-1 text-sm">
                    سوال {item.question_number ?? '—'}
                    {item.topic_title && <span className="text-slate-400"> · {item.topic_title}</span>}
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      className="btn-secondary !py-1 text-xs"
                      onClick={() => postponeReview.mutate(item.id)}
                      disabled={postponeReview.isPending}
                    >
                      بعداً
                    </button>
                    <button
                      className="btn-success !py-1 text-xs"
                      onClick={() => completeReview.mutate(item.id)}
                      disabled={completeReview.isPending}
                    >
                      الان مرور کردم
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* آزمون‌های نزدیک */}
        <div className="card">
          <h2 className="font-bold text-slate-900 mb-3">آزمون‌های پیش‌رو</h2>
          {(exams?.data ?? []).length === 0 ? (
            <p className="text-sm text-slate-400">آزمونی برنامه‌ریزی نشده است.</p>
          ) : (
            <div className="space-y-2">
              {(exams?.data ?? []).map((exam) => (
                <Link key={exam.id} to={`/exams/${exam.id}/run`}
                      className="block rounded-xl border border-slate-100 px-3 py-2 hover:border-primary-200 transition">
                  <div className="text-sm font-medium text-slate-800">{exam.title}</div>
                  <div className="text-xs text-slate-400">{exam.duration_minutes} دقیقه · {exam.question_count ?? 0} سوال</div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* خلاصه ۷ روز اخیر */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-slate-900">خلاصه ۷ روز اخیر</h2>
            <Link to="/analytics" className="text-xs text-primary-600 hover:underline">تحلیل کامل ←</Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="کل تست" value={faNumber(overview?.data?.tests?.total ?? 0)} accent="bg-primary-600" />
            <StatCard label="درست" value={faNumber(overview?.data?.tests?.correct ?? 0)} accent="bg-emerald-500" />
            <StatCard label="غلط" value={faNumber(overview?.data?.tests?.wrong ?? 0)} accent="bg-red-500" />
            <StatCard label="درصد کنکوری" value={faPercent(overview?.data?.tests?.percent_konkur ?? null)} accent="bg-amber-500" />
          </div>
        </div>

        {/* دسترسی سریع + فعالیت‌های امروز */}
        <div className="card">
          <h2 className="font-bold text-slate-900 mb-3">ثبت سریع</h2>
          <div className="grid grid-cols-2 gap-2 mb-4">
            <Link to="/tests" className="btn-primary text-xs">✏️ ثبت تست</Link>
            <Link to="/study" className="btn-secondary text-xs">📚 ثبت مطالعه</Link>
          </div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">فعالیت‌های امروز</h3>
          {recentActivities.length === 0 ? (
            <p className="text-xs text-slate-400">هنوز فعالیتی برای امروز ثبت نشده.</p>
          ) : (
            <div className="space-y-1.5">
              {recentActivities.slice(0, 5).map((a) => (
                <div key={a.id} className="flex items-center justify-between text-xs text-slate-600">
                  <span className="chip bg-slate-100">{ACTIVITY_TYPE_LABELS[a.type]}</span>
                  <span>{a.duration_minutes > 0 ? `${toFaDigits(a.duration_minutes)} دقیقه` : ''}</span>
                  <span className="text-slate-400">{timeAgo(a.started_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface OverviewData {
  tests: { total: number; correct: number; wrong: number; blank: number; percent_konkur: number | null };
  study_minutes_by_type: Record<string, number>;
  total_study_minutes: number;
  review: { pending: number; done: number };
}

interface ExamLite {
  id: string;
  title: string;
  duration_minutes: number;
  question_count?: number;
}
