// صفحه برنامه — اهداف، بلوک‌های زمانی ثابت و برنامه هفتگی (شنبه تا جمعه)
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { del, errorMessage, get, post, put } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { ConfirmButton, EmptyState, Modal, PageHeader, Spinner } from '../../components/ui';
import {
  BLOCK_TYPE_LABELS, type Goal, type Plan, type TimeBlock,
} from '../../types';
import {
  faNumber, formatJalaliLong, toFaDigits, todayISO, weekDaysISO, WEEKDAYS_SHORT, weekStartISO,
} from '../../lib/jalali';

export default function PlanningPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [weekStart, setWeekStart] = useState(weekStartISO(new Date()));
  const [tab, setTab] = useState<'week' | 'goals' | 'blocks'>('week');
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [showDayEdit, setShowDayEdit] = useState<string | null>(null);
  const [goalForm, setGoalForm] = useState({
    type: 'weekly' as Goal['type'],
    title: '',
    minutes: 120,
    start_date: todayISO(),
    end_date: todayISO(),
  });

  const days = weekDaysISO(weekStart);

  const { data: plansData, isLoading: loadingPlans } = useQuery({
    queryKey: ['week-plans', weekStart],
    queryFn: async () => {
      const results = await Promise.all(
        days.map((d) => get<Plan | null>('/plans', { date: d })),
      );
      return days.map((d, i) => ({ date: d, plan: results[i].data }));
    },
  });

  const { data: goals } = useQuery({
    queryKey: ['goals'],
    queryFn: () => get<Goal[]>('/goals'),
  });
  const { data: blocks } = useQuery({
    queryKey: ['time-blocks'],
    queryFn: () => get<TimeBlock[]>('/time-blocks'),
  });

  const generateWeek = useMutation({
    mutationFn: () => post('/plans/generate-week', { week_start: weekStart }),
    onSuccess: () => {
      toast.show('برنامه هفتگی ساخته شد — زمان‌های ثابت رعایت شد ✅');
      void queryClient.invalidateQueries({ queryKey: ['week-plans'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const saveGoal = useMutation({
    mutationFn: () =>
      post('/goals', {
        type: goalForm.type,
        title: goalForm.title,
        target_value: { minutes: goalForm.minutes },
        start_date: goalForm.start_date,
        end_date: goalForm.end_date,
      }),
    onSuccess: () => {
      toast.show('هدف ذخیره شد 🎯');
      setShowGoalForm(false);
      setGoalForm({ ...goalForm, title: '' });
      void queryClient.invalidateQueries({ queryKey: ['goals'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const deleteGoal = useMutation({
    mutationFn: (id: string) => del(`/goals/${id}`),
    onSuccess: () => {
      toast.show('هدف حذف شد.');
      void queryClient.invalidateQueries({ queryKey: ['goals'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const saveBlocks = useMutation({
    mutationFn: (rows: TimeBlock[]) =>
      put('/time-blocks', {
        blocks: rows.map((b) => ({
          day_of_week: b.day_of_week, start_time: b.start_time,
          end_time: b.end_time, block_type: b.block_type, title: b.title,
        })),
      }),
    onSuccess: () => {
      toast.show('زمان‌های ثابت ذخیره شد 🏫');
      void queryClient.invalidateQueries({ queryKey: ['time-blocks'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const saveDayPlan = useMutation({
    mutationFn: ({ date, items }: { date: string; items: Plan['items'] }) =>
      put(`/plans/${date}`, { items, status: 'active' }),
    onSuccess: () => {
      toast.show('برنامه روز ذخیره شد ✅');
      setShowDayEdit(null);
      void queryClient.invalidateQueries({ queryKey: ['week-plans'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const serverBlocks = blocks?.data ?? [];
  const [blockRows, setBlockRows] = useState<TimeBlock[]>([]);
  useEffect(() => {
    setBlockRows(serverBlocks);
  }, [blocks]);
  const weeklyGoals = (goals?.data ?? []).filter((g) => g.status === 'active');

  return (
    <div>
      <PageHeader
        title="برنامه"
        subtitle="اهداف، زمان‌های ثابت و برنامه هفتگی — هفته از شنبه شروع می‌شود"
      />

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex gap-2 bg-slate-100 rounded-xl p-1">
          {([['week', 'برنامه هفتگی'], ['goals', 'اهداف'], ['blocks', 'زمان‌های ثابت']] as const).map(
            ([key, label]) => (
              <button key={key}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${tab === key ? 'bg-white shadow text-primary-700' : 'text-slate-500'}`}
                onClick={() => setTab(key)}>
                {label}
              </button>
            ),
          )}
        </div>
        {tab === 'week' && (
          <>
            <div className="flex items-center gap-2">
              <button className="btn-secondary !py-1.5 text-xs"
                      onClick={() => setWeekStart(weekDaysISO(weekStart)[0] && new Date(new Date(weekStart).getTime() - 7 * 86400000).toISOString().slice(0, 10))}>
                → هفته قبل
              </button>
              <button className="btn-secondary !py-1.5 text-xs"
                      onClick={() => setWeekStart(weekStartISO(new Date()))}>
                این هفته
              </button>
              <button className="btn-secondary !py-1.5 text-xs"
                      onClick={() => setWeekStart(new Date(new Date(weekStart).getTime() + 7 * 86400000).toISOString().slice(0, 10))}>
                هفته بعد ←
              </button>
            </div>
            <span className="text-xs text-slate-400">
              {formatJalaliLong(days[0])} تا {formatJalaliLong(days[6])}
            </span>
            <button className="btn-primary !py-1.5 text-xs" disabled={generateWeek.isPending}
                    onClick={() => generateWeek.mutate()}>
              ✨ تولید خودکار هفته
            </button>
          </>
        )}
        {tab === 'goals' && (
          <button className="btn-primary !py-1.5 text-xs" onClick={() => setShowGoalForm(true)}>
            + هدف جدید
          </button>
        )}
        {tab === 'blocks' && (
          <button className="btn-primary !py-1.5 text-xs"
                  disabled={saveBlocks.isPending}
                  onClick={() => saveBlocks.mutate(blockRows)}>
            ذخیره زمان‌ها
          </button>
        )}
      </div>

      {tab === 'week' && (
        loadingPlans ? <Spinner /> : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {plansData?.map(({ date, plan }, i) => {
              const isToday = date === todayISO();
              return (
                <div key={date} className={`card !p-4 ${isToday ? 'border-primary-400 ring-2 ring-primary-100' : ''}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="text-sm font-bold text-slate-800">
                        {WEEKDAYS_SHORT[i]} — {formatJalaliLong(date)}
                      </div>
                      {plan && plan.summary.total_minutes > 0 && (
                        <div className="text-[11px] text-slate-400">
                          {faNumber(plan.summary.total_minutes)} دقیقه مطالعه
                        </div>
                      )}
                    </div>
                    <button className="text-xs text-primary-600 hover:underline"
                            onClick={() => setShowDayEdit(date)}>
                      ویرایش
                    </button>
                  </div>
                  {!plan || plan.items.length === 0 ? (
                    <p className="text-xs text-slate-400 py-3 text-center">برنامه‌ای ندارد</p>
                  ) : (
                    <div className="space-y-1.5">
                      {plan.items.map((item, j) => (
                        <div key={j} className="rounded-lg bg-slate-50 px-2.5 py-1.5">
                          <div className="flex items-center justify-between text-[11px] text-slate-500">
                            <span dir="ltr">{toFaDigits(item.start)}–{toFaDigits(item.end)}</span>
                            {item.subject && <span className="chip bg-primary-50 text-primary-700 !text-[10px]">{item.subject}</span>}
                          </div>
                          <div className="text-xs text-slate-700 mt-0.5">{item.title}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )
      )}

      {tab === 'goals' && (
        weeklyGoals.length === 0 ? (
          <EmptyState icon="🎯" title="هنوز هدفی تعریف نکرده‌ای"
            description="هدف بلندمدت، ماهانه یا هفتگی بساز تا برنامه‌ها با آن هم‌راستا شوند."
            action={<button className="btn-primary text-xs" onClick={() => setShowGoalForm(true)}>تعریف اولین هدف</button>} />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {weeklyGoals.map((g) => (
              <div key={g.id} className="card !p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className={`chip mb-1 ${
                      g.type === 'long' ? 'bg-purple-100 text-purple-700'
                      : g.type === 'monthly' ? 'bg-blue-100 text-blue-700'
                      : 'bg-emerald-100 text-emerald-700'}`}>
                      {g.type_label}
                    </span>
                    <div className="font-semibold text-slate-800 text-sm">{g.title}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {formatJalaliLong(g.start_date)} تا {formatJalaliLong(g.end_date)}
                      {g.target_value.minutes ? ` · ${faNumber(g.target_value.minutes)} دقیقه در روز` : ''}
                      {g.target_value.subject ? ` · ${g.target_value.subject}` : ''}
                    </div>
                  </div>
                  <ConfirmButton className="btn-danger !py-1 !px-2 text-xs" onConfirm={() => deleteGoal.mutate(g.id)}>
                    حذف
                  </ConfirmButton>
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {tab === 'blocks' && (
        <div>
          <p className="text-sm text-slate-500 mb-4 leading-relaxed">
            زمان‌های ثابت (مدرسه، کلاس) در تولید خودکار برنامه هفتگی به‌عنوان زمان اشغال‌شده در نظر گرفته می‌شوند.
            روزها از شنبه (۰) تا جمعه (۶) شماره‌گذاری می‌شوند.
          </p>
          <div className="card !p-0 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-right px-4 py-3">روز هفته</th>
                  <th className="text-right px-4 py-3">از</th>
                  <th className="text-right px-4 py-3">تا</th>
                  <th className="text-right px-4 py-3">نوع</th>
                  <th className="text-right px-4 py-3">عنوان</th>
                  <th className="text-right px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {blockRows.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    زمان ثابتی ثبت نشده — دکمه «+ افزودن» را بزن
                  </td></tr>
                )}
                {blockRows.map((b, idx) => (
                  <tr key={b.id ?? idx}>
                    <td className="px-4 py-2">
                      <select className="input !py-1 !w-28 text-xs" value={b.day_of_week}
                              onChange={(e) => updateBlock(setBlockRows, blockRows, idx, { day_of_week: Number(e.target.value) })}>
                        {WEEKDAYS_SHORT.map((w, i) => <option key={i} value={i}>{w}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2">
                      <input type="time" dir="ltr" className="input !py-1 !w-28 text-xs" value={b.start_time.slice(0, 5)}
                             onChange={(e) => updateBlock(setBlockRows, blockRows, idx, { start_time: e.target.value })} />
                    </td>
                    <td className="px-4 py-2">
                      <input type="time" dir="ltr" className="input !py-1 !w-28 text-xs" value={b.end_time.slice(0, 5)}
                             onChange={(e) => updateBlock(setBlockRows, blockRows, idx, { end_time: e.target.value })} />
                    </td>
                    <td className="px-4 py-2">
                      <select className="input !py-1 !w-28 text-xs" value={b.block_type}
                              onChange={(e) => updateBlock(setBlockRows, blockRows, idx, { block_type: e.target.value as TimeBlock['block_type'] })}>
                        {Object.entries(BLOCK_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2">
                      <input className="input !py-1 text-xs" placeholder="مثلاً مدرسه" value={b.title ?? ''}
                             onChange={(e) => updateBlock(setBlockRows, blockRows, idx, { title: e.target.value })} />
                    </td>
                    <td className="px-4 py-2">
                      <button className="text-red-500 hover:text-red-700 text-xs"
                              onClick={() => setBlockRows(blockRows.filter((_, i) => i !== idx))}>
                        حذف
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="btn-secondary mt-3 text-xs"
                  onClick={() => setBlockRows([...blockRows, {
                    id: `new-${Date.now()}`, day_of_week: 0, start_time: '07:30',
                    end_time: '13:30', block_type: 'school', title: 'مدرسه',
                  }])}>
            + افزودن زمان ثابت
          </button>
          <button className="btn-primary mt-3 mr-2 text-xs" disabled={saveBlocks.isPending}
                  onClick={() => saveBlocks.mutate(blockRows)}>
            ذخیره زمان‌ها
          </button>
        </div>
      )}

      {/* فرم هدف */}
      <Modal open={showGoalForm} onClose={() => setShowGoalForm(false)} title="هدف جدید">
        <div className="space-y-4">
          <div>
            <label className="label">نوع هدف</label>
            <div className="flex gap-1.5">
              {([['weekly', 'هفتگی'], ['monthly', 'ماهانه'], ['long', 'بلندمدت']] as const).map(([k, v]) => (
                <button key={k}
                  className={`chip border cursor-pointer ${goalForm.type === k ? 'bg-primary-600 text-white border-primary-600' : 'bg-slate-50 text-slate-600 border-slate-200'}`}
                  onClick={() => setGoalForm((f) => ({ ...f, type: k }))}>
                  {v}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">عنوان هدف</label>
            <input className="input" value={goalForm.title}
                   onChange={(e) => setGoalForm((f) => ({ ...f, title: e.target.value }))}
                   placeholder="مثلاً: ۱۰ تست حد با دقت ۸۰٪" />
          </div>
          <div>
            <label className="label">سهم روزانه (دقیقه) — در تولید برنامه استفاده می‌شود</label>
            <input type="number" className="input" dir="ltr" min={15} max={720}
                   value={goalForm.minutes}
                   onChange={(e) => setGoalForm((f) => ({ ...f, minutes: Number(e.target.value) }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">از تاریخ</label>
              <input type="date" className="input" dir="ltr" value={goalForm.start_date}
                     onChange={(e) => setGoalForm((f) => ({ ...f, start_date: e.target.value }))} />
            </div>
            <div>
              <label className="label">تا تاریخ</label>
              <input type="date" className="input" dir="ltr" value={goalForm.end_date}
                     onChange={(e) => setGoalForm((f) => ({ ...f, end_date: e.target.value }))} />
            </div>
          </div>
          <button className="btn-primary w-full" disabled={saveGoal.isPending || !goalForm.title.trim()}
                  onClick={() => saveGoal.mutate()}>
            ذخیره هدف
          </button>
        </div>
      </Modal>

      {/* ویرایش برنامه روز */}
      <DayEditModal
        date={showDayEdit}
        onClose={() => setShowDayEdit(null)}
        plansData={plansData ?? []}
        onSave={(date, items) => saveDayPlan.mutate({ date, items })}
        saving={saveDayPlan.isPending}
      />
    </div>
  );
}

// --- helpers برای جدول بلوک‌ها ---
function updateBlock(
  setter: (rows: TimeBlock[]) => void,
  rows: TimeBlock[],
  idx: number,
  patch: Partial<TimeBlock>,
) {
  setter(rows.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
}


function DayEditModal({ date, onClose, plansData, onSave, saving }: {
  date: string | null;
  onClose: () => void;
  plansData: { date: string; plan: Plan | null }[];
  onSave: (date: string, items: Plan['items']) => void;
  saving: boolean;
}) {
  const current = plansData.find((p) => p.date === date)?.plan;
  const [items, setItems] = useState<Plan['items']>([]);

  useEffect(() => {
    setItems(current ? JSON.parse(JSON.stringify(current.items)) : []);
  }, [date, current]);

  if (!date) return null;

  const updateItem = (idx: number, patch: Partial<Plan['items'][number]>) => {
    setItems((prev) => prev.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
  };

  return (
    <Modal open onClose={onClose} title={`ویرایش برنامه ${formatJalaliLong(date)}`} wide>
      <div className="space-y-3">
        {items.length === 0 && (
          <p className="text-sm text-slate-400">آیتمی نیست — با دکمه پایین اضافه کن.</p>
        )}
        {items.map((item, idx) => (
          <div key={idx} className="grid grid-cols-12 gap-2 items-center">
            <input type="time" dir="ltr" className="input !py-1.5 text-xs col-span-2" value={item.start}
                   onChange={(e) => updateItem(idx, { start: e.target.value })} />
            <input type="time" dir="ltr" className="input !py-1.5 text-xs col-span-2" value={item.end}
                   onChange={(e) => updateItem(idx, { end: e.target.value })} />
            <input className="input !py-1.5 text-xs col-span-5" value={item.title}
                   onChange={(e) => updateItem(idx, { title: e.target.value })} placeholder="عنوان" />
            <input className="input !py-1.5 text-xs col-span-2" value={item.subject ?? ''}
                   onChange={(e) => updateItem(idx, { subject: e.target.value })} placeholder="درس" />
            <button className="text-red-500 hover:text-red-700 text-xs col-span-1"
                    onClick={() => setItems((prev) => prev.filter((_, i) => i !== idx))}>
              حذف
            </button>
          </div>
        ))}
        <div className="flex gap-2">
          <button className="btn-secondary text-xs"
                  onClick={() => setItems((prev) => [...prev, {
                    start: '16:00', end: '17:00', title: '', subject: '', type: 'study', done: false,
                  }])}>
            + افزودن آیتم
          </button>
          <button className="btn-primary text-xs" disabled={saving}
                  onClick={() => onSave(date, items)}>
            ذخیره برنامه
          </button>
        </div>
      </div>
    </Modal>
  );
}
