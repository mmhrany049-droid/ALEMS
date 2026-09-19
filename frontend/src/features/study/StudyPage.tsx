// صفحه مطالعه — ثبت فعالیت و مشاهده منابع
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { errorMessage, get, post } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, Modal, PageHeader, Spinner } from '../../components/ui';
import { ACTIVITY_TYPE_LABELS, type Activity, type Resource, type Subject } from '../../types';
import { faNumber, formatJalali, formatMinutes, timeAgo, toFaDigits } from '../../lib/jalali';

const TYPES = ['study', 'test', 'review', 'class', 'school'] as const;

export default function StudyPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    type: 'study' as (typeof TYPES)[number],
    subject_id: '',
    resource_id: '',
    duration_minutes: 45,
    note: '',
  });

  const { data: activities, isLoading } = useQuery({
    queryKey: ['activities'],
    queryFn: () => get<Activity[]>('/activities', { page_size: 30 }),
  });
  const { data: subjects } = useQuery({
    queryKey: ['subjects'],
    queryFn: () => get<Subject[]>('/subjects'),
  });
  const { data: resources } = useQuery({
    queryKey: ['resources'],
    queryFn: () => get<Resource[]>('/resources'),
  });

  const addActivity = useMutation({
    mutationFn: () =>
      post('/activities', {
        type: form.type,
        subject_id: form.subject_id || undefined,
        resource_id: form.resource_id || undefined,
        duration_minutes: form.duration_minutes,
        note: form.note || undefined,
      }),
    onSuccess: () => {
      toast.show('فعالیت ثبت شد ✅');
      setShowForm(false);
      setForm({ ...form, duration_minutes: 45, note: '' });
      void queryClient.invalidateQueries({ queryKey: ['activities'] });
      void queryClient.invalidateQueries({ queryKey: ['overview-7d'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  return (
    <div>
      <PageHeader
        title="مطالعه"
        subtitle="ثبت جلسات مطالعه، کلاس و فعالیت‌های تحصیلی"
        actions={
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + ثبت فعالیت
          </button>
        }
      />

      {/* منابع */}
      <h2 className="font-bold text-slate-900 mb-3">منابع من</h2>
      {(resources?.data ?? []).length === 0 ? (
        <div className="card mb-6 text-sm text-slate-500">
          هنوز منبعی وارد نکرده‌ای. کتاب تست را از بخش «تست‌ها» وارد کن.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-8">
          {(resources?.data ?? []).slice(0, 6).map((r) => (
            <div key={r.id} className="card !p-4">
              <div className="font-semibold text-slate-800 text-sm mb-1">{r.title}</div>
              <div className="text-xs text-slate-400">
                {r.publisher ? `${r.publisher} · ` : ''}{faNumber(r.question_count ?? 0)} سوال
              </div>
            </div>
          ))}
        </div>
      )}

      {/* فعالیت‌ها */}
      <h2 className="font-bold text-slate-900 mb-3">فعالیت‌های اخیر</h2>
      {isLoading ? (
        <Spinner />
      ) : (activities?.data ?? []).length === 0 ? (
        <EmptyState
          icon="📚"
          title="هنوز فعالیتی ثبت نکرده‌ای"
          description="اولین جلسه مطالعه‌ات را ثبت کن تا آمار و نمودارهایت ساخته شود."
          action={<button className="btn-primary text-xs" onClick={() => setShowForm(true)}>ثبت اولین فعالیت</button>}
        />
      ) : (
        <div className="card !p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs">
              <tr>
                <th className="text-right px-4 py-3">نوع</th>
                <th className="text-right px-4 py-3">درس</th>
                <th className="text-right px-4 py-3">مدت</th>
                <th className="text-right px-4 py-3">یادداشت</th>
                <th className="text-right px-4 py-3">زمان</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(activities?.data ?? []).map((a) => (
                <tr key={a.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3">
                    <span className={`chip ${
                      a.type === 'study' ? 'bg-blue-100 text-blue-700'
                      : a.type === 'test' ? 'bg-amber-100 text-amber-700'
                      : a.type === 'review' ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-slate-100 text-slate-600'}`}>
                      {ACTIVITY_TYPE_LABELS[a.type]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{a.subject_name ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-700">{formatMinutes(a.duration_minutes)}</td>
                  <td className="px-4 py-3 text-slate-500 max-w-48 truncate">{a.note ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{timeAgo(a.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* فرم ثبت فعالیت */}
      <Modal open={showForm} onClose={() => setShowForm(false)} title="ثبت فعالیت جدید">
        <div className="space-y-4">
          <div>
            <label className="label">نوع فعالیت</label>
            <div className="flex flex-wrap gap-1.5">
              {TYPES.map((t) => (
                <button key={t}
                  className={`chip border cursor-pointer ${form.type === t ? 'bg-primary-600 text-white border-primary-600' : 'bg-slate-50 text-slate-600 border-slate-200'}`}
                  onClick={() => setForm((f) => ({ ...f, type: t }))}>
                  {ACTIVITY_TYPE_LABELS[t]}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">درس (اختیاری)</label>
            <select className="input" value={form.subject_id}
                    onChange={(e) => setForm((f) => ({ ...f, subject_id: e.target.value }))}>
              <option value="">— انتخاب نکن —</option>
              {(subjects?.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.field} · {s.grade})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">مدت (دقیقه)</label>
            <input type="number" className="input" dir="ltr" min={0} max={1440}
                   value={form.duration_minutes}
                   onChange={(e) => setForm((f) => ({ ...f, duration_minutes: Number(e.target.value) }))} />
          </div>
          <div>
            <label className="label">یادداشت (اختیاری)</label>
            <textarea className="input" rows={2} value={form.note}
                      onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
                      placeholder="مثلاً: حل تمرین‌های فصل حد" />
          </div>
          <button className="btn-primary w-full" disabled={addActivity.isPending}
                  onClick={() => addActivity.mutate()}>
            ثبت فعالیت
          </button>
        </div>
      </Modal>
    </div>
  );
}
