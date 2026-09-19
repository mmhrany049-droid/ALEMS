// صفحه تحلیل — نمودارهای خطی/میله‌ای/دایره‌ای + جداول عملکرد
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { downloadFile, errorMessage, get } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, PageHeader, Spinner } from '../../components/ui';
import type { MistakeStat, SubjectStat, TopicStat } from '../../types';
import { faNumber, faPercent, formatJalali, toFaDigits } from '../../lib/jalali';

const COLORS = ['#2747e6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'];

interface Overview {
  tests: { total: number; correct: number; wrong: number; blank: number; percent_konkur: number | null };
  study_minutes_by_type: Record<string, number>;
  total_study_minutes: number;
  review: { pending: number; done: number };
}

interface DifficultyRow {
  difficulty: string;
  label: string;
  total: number;
  correct: number;
  wrong: number;
  blank: number;
  percent_konkur: number | null;
}

export default function AnalyticsPage() {
  const [range, setRange] = useState<7 | 30 | 0>(30);
  const [downloading, setDownloading] = useState(false);
  const toast = useToast();

  const handleDownload = async (kind: 'pdf' | 'excel') => {
    setDownloading(true);
    try {
      await downloadFile(`/api/v1/export/${kind}?type=weekly`,
        kind === 'pdf' ? 'alems-weekly.pdf' : 'alems-weekly.xlsx');
      toast.show(kind === 'pdf' ? 'PDF گزارش هفتگی دانلود شد 📄' : 'Excel گزارش هفتگی دانلود شد 📊');
    } catch (e) {
      toast.show(errorMessage(e), 'error');
    } finally {
      setDownloading(false);
    }
  };

  const toDate = new Date().toISOString().slice(0, 10);
  const fromDate = range > 0 ? new Date(Date.now() - (range - 1) * 86400000).toISOString().slice(0, 10) : undefined;
  const rangeParams = { from: fromDate, to: toDate };

  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['analytics-overview', range],
    queryFn: () => get<Overview>('/analytics/overview', rangeParams),
  });
  const { data: bySubject, isLoading: loadingSubject } = useQuery({
    queryKey: ['analytics-subject', range],
    queryFn: () => get<SubjectStat[]>('/analytics/by-subject', rangeParams),
  });
  const weekly = useQuery({
    queryKey: ['weekly-report'],
    queryFn: () => get<WeeklyReport>('/reports/weekly'),
  });
  const { data: byTopic } = useQuery({
    queryKey: ['analytics-topic', range],
    queryFn: () => get<TopicStat[]>('/analytics/by-topic', rangeParams),
  });
  const { data: difficulty } = useQuery({
    queryKey: ['analytics-difficulty', range],
    queryFn: () => get<DifficultyRow[]>('/analytics/difficulty', rangeParams),
  });
  const { data: mistakes } = useQuery({
    queryKey: ['analytics-mistakes', range],
    queryFn: () => get<MistakeStat[]>('/analytics/mistake-types', rangeParams),
  });

  // روند هفتگی ۸ هفته اخیر (خطی)
  const { data: trend } = useQuery({
    queryKey: ['analytics-trend'],
    queryFn: async () => {
      const weeks: { name: string; percent: number | null; total: number }[] = [];
      for (let i = 7; i >= 0; i--) {
        const to = new Date(Date.now() - i * 7 * 86400000).toISOString().slice(0, 10);
        const from = new Date(Date.now() - (i * 7 + 6) * 86400000).toISOString().slice(0, 10);
        const r = await get<Overview>('/analytics/overview', { from, to });
        weeks.push({
          name: formatJalali(to).slice(0, -3),
          percent: r.data.tests.percent_konkur,
          total: r.data.tests.total,
        });
      }
      return weeks;
    },
  });

  const subjectRows = bySubject?.data ?? [];
  const mistakeRows = mistakes?.data ?? [];
  const diffRows = difficulty?.data ?? [];
  const hasData = (overview?.data?.tests?.total ?? 0) > 0;

  return (
    <div>
      <PageHeader
        title="تحلیل"
        subtitle="عملکرد خود را ببینید؛ نقاط ضعف را پیدا کنید"
        actions={
          <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
            {([[7, '۷ روز'], [30, '۳۰ روز'], [0, 'همه']] as const).map(([key, label]) => (
              <button key={key}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${range === key ? 'bg-white shadow text-primary-700' : 'text-slate-500'}`}
                onClick={() => setRange(key)}>
                {label}
              </button>
            ))}
          </div>
        }
      />

      {loadingOverview ? <Spinner /> : !hasData ? (
        <EmptyState icon="📊" title="هنوز داده‌ای برای تحلیل نیست"
          description="با ثبت تست، آمار و نمودارهای عملکردت اینجا ساخته می‌شود."
        />
      ) : (
        <div className="space-y-6">
          {/* گزارش هفتگی + خروجی PDF/Excel */}
          <div className="card">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <div>
                <h2 className="font-bold text-slate-900">گزارش هفتگی</h2>
                {weekly.data?.data && (
                  <p className="text-xs text-slate-400 mt-0.5">
                    هفته {weekly.data.data.week_start_label} تا {weekly.data.data.week_end_label}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary !py-1.5 text-xs"
                        disabled={downloading}
                        onClick={() => handleDownload('pdf')}>
                  📄 خروجی PDF
                </button>
                <button className="btn-secondary !py-1.5 text-xs"
                        disabled={downloading}
                        onClick={() => handleDownload('excel')}>
                  📊 خروجی Excel
                </button>
              </div>
            </div>
            {weekly.isLoading ? <Spinner /> : weekly.data?.data ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-100">
                      <th className="text-right px-3 py-2 font-medium">روز</th>
                      <th className="text-right px-3 py-2 font-medium">تست‌ها</th>
                      <th className="text-right px-3 py-2 font-medium">درصد کنکوری</th>
                      <th className="text-right px-3 py-2 font-medium">مطالعه</th>
                    </tr>
                  </thead>
                  <tbody>
                    {weekly.data.data.per_day.map((d) => (
                      <tr key={d.date} className="border-b border-slate-50">
                        <td className="px-3 py-2 text-slate-700">{d.date_label}</td>
                        <td className="px-3 py-2 text-slate-600">{toFaDigits(d.tests.total)}</td>
                        <td className="px-3 py-2 font-bold">
                          <span className={d.tests.percent_konkur !== null && d.tests.percent_konkur < 0 ? 'text-red-600' : 'text-emerald-600'}>
                            {faPercent(d.tests.percent_konkur)}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-slate-600">{toFaDigits(d.activities_minutes)} دقیقه</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="text-xs text-slate-400">گزارش در دسترس نیست.</p>}
          </div>

          {/* نمودار خطی روند */}
          <div className="card">
            <h2 className="font-bold text-slate-900 mb-4">روند درصد کنکوری (۸ هفته اخیر)</h2>
            <div className="h-64" dir="ltr">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fontFamily: 'Vazirmatn' }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[-20, 100]} />
                  <Tooltip contentStyle={{ fontFamily: 'Vazirmatn', direction: 'rtl' }} />
                  <Line type="monotone" dataKey="percent" name="درصد کنکوری"
                        stroke="#2747e6" strokeWidth={2.5} dot={{ r: 4 }} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            {/* میله‌ای به تفکیک درس */}
            <div className="card">
              <h2 className="font-bold text-slate-900 mb-4">درصد به تفکیک درس</h2>
              {subjectRows.length === 0 ? (
                <p className="text-sm text-slate-400 py-8 text-center">داده‌ای نیست</p>
              ) : (
                <div className="h-64" dir="ltr">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={subjectRows}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="subject" tick={{ fontSize: 11, fontFamily: 'Vazirmatn' }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ fontFamily: 'Vazirmatn', direction: 'rtl' }} />
                      <Bar dataKey="percent_konkur" name="درصد کنکوری" radius={[6, 6, 0, 0]}>
                        {subjectRows.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* دایره‌ای نوع اشتباهات */}
            <div className="card">
              <h2 className="font-bold text-slate-900 mb-4">نوع اشتباهات</h2>
              {mistakeRows.length === 0 ? (
                <p className="text-sm text-slate-400 py-8 text-center">
                  هنوز غلطی با نوع مشخص ثبت نشده — در ثبت تست، نوع اشتباه را انتخاب کن.
                </p>
              ) : (
                <div className="h-64" dir="ltr">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={mistakeRows} dataKey="count" nameKey="label"
                           innerRadius={50} outerRadius={85} paddingAngle={3}>
                        {mistakeRows.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ fontFamily: 'Vazirmatn', direction: 'rtl' }} />
                      <Legend formatter={(v) => <span style={{ fontFamily: 'Vazirmatn', fontSize: 12 }}>{v}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          {/* سختی */}
          <div className="card">
            <h2 className="font-bold text-slate-900 mb-4">عملکرد بر اساس سختی</h2>
            <div className="grid grid-cols-3 gap-3">
              {diffRows.map((d) => (
                <div key={d.difficulty} className="rounded-xl border border-slate-100 p-4 text-center">
                  <div className="text-sm text-slate-500 mb-1">{d.label}</div>
                  <div className="text-2xl font-bold text-slate-900">{faPercent(d.percent_konkur)}</div>
                  <div className="text-xs text-slate-400 mt-1">{faNumber(d.total)} سوال</div>
                </div>
              ))}
            </div>
          </div>

          {/* جدول دروس */}
          <div>
            <h2 className="font-bold text-slate-900 mb-3">عملکرد به تفکیک درس (AT-23)</h2>
            {loadingSubject ? <Spinner /> : (
              <div className="card !p-0 overflow-x-auto">
                <table className="w-full text-sm min-w-125">
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
                    {subjectRows.length === 0 && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-400">داده‌ای نیست</td></tr>
                    )}
                    {subjectRows.map((s) => (
                      <tr key={s.subject} className="hover:bg-slate-50/60">
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

          {/* جدول مباحث ضعیف */}
          <div>
            <h2 className="font-bold text-slate-900 mb-3">مباحث نیازمند تمرین بیشتر</h2>
            <div className="card !p-0 overflow-x-auto">
              <table className="w-full text-sm min-w-125">
                <thead className="bg-slate-50 text-slate-500 text-xs">
                  <tr>
                    <th className="text-right px-4 py-3">مبحث</th>
                    <th className="text-right px-4 py-3">فصل</th>
                    <th className="text-right px-4 py-3">درس</th>
                    <th className="text-right px-4 py-3">کل</th>
                    <th className="text-right px-4 py-3">درصد کنکوری</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(byTopic?.data ?? []).length === 0 && (
                    <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">داده‌ای نیست</td></tr>
                  )}
                  {(byTopic?.data ?? []).slice(0, 10).map((t) => (
                    <tr key={t.topic_id} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3 font-medium">{t.topic}</td>
                      <td className="px-4 py-3 text-slate-500">{t.chapter}</td>
                      <td className="px-4 py-3 text-slate-500">{t.subject}</td>
                      <td className="px-4 py-3">{faNumber(t.total)}</td>
                      <td className={`px-4 py-3 font-bold ${
                        t.percent_konkur !== null && t.percent_konkur < 40 ? 'text-red-600' : 'text-slate-700'
                      }`}>
                        {faPercent(t.percent_konkur)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface WeeklyReportDay {
  date: string; date_label: string;
  tests: { total: number; correct: number; wrong: number; blank: number; percent_konkur: number | null };
  activities_minutes: number;
}
interface WeeklyReport {
  week_start_label: string; week_end_label: string;
  per_day: WeeklyReportDay[];
  tests: { total: number; correct: number; wrong: number; blank: number; percent_konkur: number | null };
  review: { pending: number; done: number };
  by_subject: { subject: string; total: number; percent_konkur: number | null }[];
}
