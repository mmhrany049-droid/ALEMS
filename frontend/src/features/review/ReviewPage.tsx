// صفحه مرور — صف مرور با اولویت واضح (۷.۴) + بازسازی صف
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { errorMessage, get, post } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, PageHeader, Spinner, StatCard } from '../../components/ui';
import {
  DIFFICULTY_LABELS, MARK_COLORS, MARK_LABELS, type MarkType, type ReviewItem,
} from '../../types';
import { faNumber, formatJalali, toFaDigits } from '../../lib/jalali';

const REASON_LABELS: Record<string, string> = {
  wrong: 'غلط',
  blank: 'نزده',
  mark_important: 'مهم',
  mark_hard: 'سخت',
  mark_review: 'نیاز به مرور',
};

export default function ReviewPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<'pending' | 'done' | 'all'>('pending');

  const { data, isLoading } = useQuery({
    queryKey: ['review-queue', status],
    queryFn: () => get<ReviewItem[]>('/reviews/queue', { status }),
  });

  const { data: allPending } = useQuery({
    queryKey: ['review-queue', 'pending'],
    queryFn: () => get<ReviewItem[]>('/reviews/queue', { status: 'pending' }),
  });

  const complete = useMutation({
    mutationFn: (id: string) => post(`/reviews/${id}/complete`),
    onSuccess: () => {
      toast.show('مرور شد! مرور بعدی طبق چرخه ۱-۳-۷-۱۴ برنامه‌ریزی می‌شود ✅');
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const postponed = useMutation({
    mutationFn: ({ id, days }: { id: string; days?: number }) =>
      post(`/reviews/${id}/postpone`, { days: days ?? 1 }),
    onSuccess: () => {
      toast.show('مرور برای بعد به‌عقب افتاد ⏭');
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const reopen = useMutation({
    mutationFn: (id: string) => post(`/reviews/${id}/reopen`),
    onSuccess: () => {
      toast.show('سوال به صف مرور برگشت.');
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const rebuild = useMutation({
    mutationFn: () => post<{ added: number; removed: number; pending: number }>('/reviews/rebuild'),
    onSuccess: (r) => {
      const d = r.data;
      toast.show(`صف مرور بازسازی شد — ${toFaDigits(d.added)} مورد جدید، ${toFaDigits(d.removed)} حذف شد`);
      void queryClient.invalidateQueries({ queryKey: ['review-queue'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const items = data?.data ?? [];
  const pendingCount = (allPending?.data ?? []).length;

  return (
    <div>
      <PageHeader
        title="مرور"
        subtitle="صف مرور بر اساس غلط‌ها، نزده‌ها و تیک‌های مهم/سخت/مرور ساخته می‌شود"
        actions={
          <button className="btn-secondary" disabled={rebuild.isPending}
                  onClick={() => rebuild.mutate()}>
            🔄 بازسازی صف
          </button>
        }
      />

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
        <StatCard label="در انتظار مرور" value={faNumber(pendingCount)} accent="bg-red-500" />
        <StatCard label="چرخه مرور" value={<>۱ → ۳ → ۷ → ۱۴ روز</>} accent="bg-blue-500" hint="تکرار با فاصله" />
        <StatCard label="قانون" value="غلط + تیک‌ها" accent="bg-primary-600" hint="نزده‌ها اختیاری (از تنظیمات)" />
      </div>

      <div className="flex gap-2 mb-4 bg-slate-100 rounded-xl p-1 w-fit">
        {([['pending', 'در انتظار'], ['done', 'مرور شده'], ['all', 'همه']] as const).map(([key, label]) => (
          <button key={key}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${status === key ? 'bg-white shadow text-primary-700' : 'text-slate-500'}`}
            onClick={() => setStatus(key)}>
            {label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🎉"
          title={status === 'pending' ? 'صف مرور خالی است' : 'موردی یافت نشد'}
          description={status === 'pending'
            ? 'الان چیزی برای مرور نداری. با زدن تست و علامت‌گذاری سوالات مهم، صف مرور ساخته می‌شود.'
            : 'با تغییر فیلتر، موارد دیگر را ببین.'}
        />
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id}
                 className={`card !p-4 flex flex-wrap items-center gap-3 ${item.status === 'done' ? 'opacity-60' : ''}`}>
              <span className="size-8 rounded-lg bg-primary-50 text-primary-700 grid place-items-center text-xs font-bold shrink-0">
                {toFaDigits(item.priority)}
              </span>
              <div className="flex-1 min-w-40">
                <div className="text-sm font-medium text-slate-800">
                  سوال {item.question_number ?? '—'}
                  {item.topic_title && <span className="text-slate-400 font-normal"> · {item.topic_title}</span>}
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  <span className={`chip ${
                    item.reason === 'wrong' ? 'bg-red-100 text-red-700'
                    : item.reason === 'blank' ? 'bg-slate-100 text-slate-600'
                    : 'bg-blue-100 text-blue-700'}`}>
                    {REASON_LABELS[item.reason] ?? item.reason}
                  </span>
                  {item.difficulty && (
                    <span className="chip bg-slate-100 text-slate-600">{DIFFICULTY_LABELS[item.difficulty]}</span>
                  )}
                  {item.marks.map((m) => (
                    <span key={m} className={`chip border ${MARK_COLORS[m as MarkType] ?? ''}`}>
                      {MARK_LABELS[m as MarkType] ?? m}
                    </span>
                  ))}
                  {item.review_count > 0 && (
                    <span className="chip bg-emerald-50 text-emerald-700">
                      {toFaDigits(item.review_count)} بار مرور شده
                    </span>
                  )}
                </div>
              </div>
              <div className="text-xs text-slate-400">
                {formatJalali(item.scheduled_date)}
              </div>
              {item.status === 'pending' ? (
                <div className="flex gap-1.5">
                  <button className="btn-secondary !py-1.5 text-xs"
                          disabled={postponed.isPending}
                          title="به‌عقب‌انداختن به فردا"
                          onClick={() => postponed.mutate({ id: item.id })}>
                    بعداً
                  </button>
                  <button className="btn-success !py-1.5 text-xs"
                          disabled={complete.isPending}
                          onClick={() => complete.mutate(item.id)}>
                    ✓ مرور شد
                  </button>
                </div>
              ) : (
                <button className="btn-secondary !py-1.5 text-xs"
                        disabled={reopen.isPending}
                        onClick={() => reopen.mutate(item.id)}>
                  بازگشت به صف
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
