// تنظیمات — پروفایل، سیاست‌ها، Backup/Restore، خروجی داده
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { downloadFile, errorMessage, get, post, put } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { ConfirmButton, EmptyState, PageHeader, Spinner } from '../../components/ui';
import { useAuth } from '../../hooks/useAuth';
import {
  FIELDS, GRADES, type BackupInfo, type Profile, type StudentState,
} from '../../types';
import { faNumber, formatJalali, formatJalaliLong, timeAgo } from '../../lib/jalali';

interface SettingsData {
  scoring_policy: { wrong_penalty: number };
  review_policy: { include_blank: boolean; intervals_days: number[] };
  exam_policy: { max_questions: number };
}

export default function SettingsPage() {
  const toast = useToast();
  const { profile, refresh } = useAuth();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'profile' | 'policies' | 'data'>('profile');
  const [form, setForm] = useState({
    full_name: '', grade: 'دوازدهم', field: 'ریاضی',
    academic_year: '', target_rank: '', target_major: '',
  });
  const [backupPassword, setBackupPassword] = useState('');

  useEffect(() => {
    if (profile) {
      setForm({
        full_name: profile.full_name ?? '',
        grade: profile.grade ?? 'دوازدهم',
        field: profile.field ?? 'ریاضی',
        academic_year: profile.academic_year ?? '',
        target_rank: profile.target_rank?.toString() ?? '',
        target_major: profile.target_major ?? '',
      });
    }
  }, [profile]);

  const { data: settingsData } = useQuery({
    queryKey: ['settings'],
    queryFn: () => get<SettingsData>('/settings'),
  });
  const { data: backups } = useQuery({
    queryKey: ['backups'],
    queryFn: () => get<BackupInfo[]>('/backup/list'),
    enabled: tab === 'data',
  });
  const { data: states } = useQuery({
    queryKey: ['states-recent'],
    queryFn: () => {
      const from = new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10);
      const to = new Date().toISOString().slice(0, 10);
      return get<StudentState[]>('/students/me/state', { from, to });
    },
    enabled: tab === 'profile',
  });

  const saveProfile = useMutation({
    mutationFn: () =>
      put('/students/me', {
        full_name: form.full_name,
        grade: form.grade,
        field: form.field,
        academic_year: form.academic_year || undefined,
        target_rank: form.target_rank ? Number(form.target_rank) : undefined,
        target_major: form.target_major || undefined,
      }),
    onSuccess: async () => {
      toast.show('پروفایل ذخیره شد ✅');
      await refresh();
      void queryClient.invalidateQueries({ queryKey: ['states-recent'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const savePolicy = useMutation({
    mutationFn: (payload: Partial<SettingsData>) => put('/settings', payload),
    onSuccess: () => {
      toast.show('تنظیمات ذخیره شد ✅');
      void queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const createBackup = useMutation({
    mutationFn: (encrypted: boolean) =>
      post<BackupInfo>('/backup/create', {
        encrypted,
        password: encrypted ? backupPassword || undefined : undefined,
      }),
    onSuccess: (r) => {
      toast.show(`پشتیبان «${r.data.filename}» ساخته شد 💾`);
      void queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const restore = useMutation({
    mutationFn: (id: string) => post('/backup/restore', { backup_id: id, confirm: true }),
    onSuccess: () => {
      toast.show('بازگردانی کامل شد ✅ — صفحه بارگذاری مجدد می‌شود');
      setTimeout(() => window.location.reload(), 1500);
    },
    onError: (e) => toast.show(errorMessage(e), 'error'),
  });

  const download = async (url: string, name: string, successMsg: string) => {
    try {
      await downloadFile(url, name);
      toast.show(successMsg);
    } catch (e) {
      toast.show(errorMessage(e), 'error');
    }
  };

  return (
    <div>
      <PageHeader title="تنظیمات" subtitle="پروفایل، سیاست‌های برنامه و مدیریت داده‌ها" />

      <div className="flex gap-2 mb-5 bg-slate-100 rounded-xl p-1 w-fit">
        {([['profile', 'پروفایل'], ['policies', 'سیاست‌ها'], ['data', 'داده‌ها و پشتیبان']] as const).map(
          ([key, label]) => (
            <button key={key}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${tab === key ? 'bg-white shadow text-primary-700' : 'text-slate-500'}`}
              onClick={() => setTab(key)}>
              {label}
            </button>
          ),
        )}
      </div>

      {tab === 'profile' && (
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="card lg:col-span-2">
            <h2 className="font-bold text-slate-900 mb-4">پروفایل دانش‌آموز</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">نام کامل</label>
                <input className="input" value={form.full_name}
                       onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
              </div>
              <div>
                <label className="label">سال تحصیلی</label>
                <input className="input" placeholder="مثلاً ۱۴۰۴-۱۴۰۵" value={form.academic_year}
                       onChange={(e) => setForm((f) => ({ ...f, academic_year: e.target.value }))} />
              </div>
              <div>
                <label className="label">پایه</label>
                <select className="input" value={form.grade}
                        onChange={(e) => setForm((f) => ({ ...f, grade: e.target.value }))}>
                  {GRADES.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div>
                <label className="label">رشته</label>
                <select className="input" value={form.field}
                        onChange={(e) => setForm((f) => ({ ...f, field: e.target.value }))}>
                  {FIELDS.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
              <div>
                <label className="label">رتبه هدف (اختیاری)</label>
                <input className="input" dir="ltr" type="number" min={1} value={form.target_rank}
                       onChange={(e) => setForm((f) => ({ ...f, target_rank: e.target.value }))}
                       placeholder="مثلاً ۱۰۰۰" />
              </div>
              <div>
                <label className="label">رشته دانشگاهی هدف (اختیاری)</label>
                <input className="input" value={form.target_major}
                       onChange={(e) => setForm((f) => ({ ...f, target_major: e.target.value }))}
                       placeholder="مثلاً کامپیوتر" />
              </div>
            </div>
            <button className="btn-primary mt-4" disabled={saveProfile.isPending}
                    onClick={() => saveProfile.mutate()}>
              ذخیره پروفایل
            </button>
          </div>

          <div className="card">
            <h2 className="font-bold text-slate-900 mb-3">وضعیت روزانه اخیر</h2>
            {(states?.data ?? []).length === 0 ? (
              <p className="text-sm text-slate-400">هنوز وضعیتی ثبت نشده — از صفحه «امروز» ثبت کن.</p>
            ) : (
              <div className="space-y-2">
                {(states?.data ?? []).slice().reverse().map((s) => (
                  <div key={s.id} className="flex items-center justify-between text-xs">
                    <span className="text-slate-600">{formatJalaliLong(s.date)}</span>
                    <span className="flex gap-1">
                      {Array.from({ length: 5 }, (_, i) => (
                        <span key={i} className={`size-2 rounded-full ${i < s.energy_level ? 'bg-emerald-500' : 'bg-slate-200'}`} />
                      ))}
                    </span>
                    <span className="text-slate-400">{s.mood ?? '—'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'policies' && settingsData && (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="card">
            <h2 className="font-bold text-slate-900 mb-2">نمره‌دهی</h2>
            <p className="text-xs text-slate-400 mb-4">
              ضریب نمره منفی در فرمول (درست − ضریب × غلط) ÷ کل × ۱۰۰
            </p>
            <label className="label">ضریب غلط: {faNumber(settingsData.data.scoring_policy.wrong_penalty)}</label>
            <input type="range" min={0} max={1} step={0.01} dir="ltr"
                   defaultValue={settingsData.data.scoring_policy.wrong_penalty}
                   onChange={(e) => setPolicyLocal({ wrong_penalty: Number(e.target.value) })}
                   className="w-full accent-primary-600" />
            <PolicySave localState={policyLocalState} onSave={(p) => savePolicy.mutate(p)} />
          </div>

          <div className="card">
            <h2 className="font-bold text-slate-900 mb-2">مرور</h2>
            <p className="text-xs text-slate-400 mb-4">قوانین ساخت صف مرور</p>
            <label className="flex items-center gap-2 mb-3 text-sm cursor-pointer">
              <input type="checkbox" defaultChecked={settingsData.data.review_policy.include_blank}
                     onChange={(e) => setPolicyLocal({ include_blank: e.target.checked })}
                     className="size-4 accent-primary-600" />
              سوالات «نزده» هم وارد صف مرور شوند
            </label>
            <label className="label">چرخه مرور (روز)</label>
            <input className="input" dir="ltr"
                   defaultValue={settingsData.data.review_policy.intervals_days.join(', ')}
                   onChange={(e) => setPolicyLocal({
                     intervals: e.target.value.split(',').map((x) => Number(x.trim())).filter((n) => n > 0),
                   })}
                   placeholder="1, 3, 7, 14" />
            <PolicySave localState={policyLocalState} onSave={(p) => savePolicy.mutate(p)} />
          </div>

          <div className="card">
            <h2 className="font-bold text-slate-900 mb-2">آزمون</h2>
            <label className="label">حداکثر تعداد سوال هر آزمون</label>
            <input type="number" className="input" dir="ltr" min={1} max={500}
                   defaultValue={settingsData.data.exam_policy.max_questions}
                   onChange={(e) => setPolicyLocal({ max_questions: Number(e.target.value) })} />
            <PolicySave localState={policyLocalState} onSave={(p) => savePolicy.mutate(p)} />
          </div>
        </div>
      )}

      {tab === 'data' && (
        <div className="grid gap-5 lg:grid-cols-2">
          {/* خروجی */}
          <div className="card">
            <h2 className="font-bold text-slate-900 mb-2">خروجی داده</h2>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              داده‌ها متعلق به توست — هر زمان می‌توانی کامل‌شان را بگیری (AT-25/26).
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button className="btn-secondary text-xs"
                      onClick={() => download('/api/v1/export/pdf?type=weekly', 'alems-weekly.pdf', 'PDF هفتگی دانلود شد 📄')}>
                📄 گزارش PDF
              </button>
              <button className="btn-secondary text-xs"
                      onClick={() => download('/api/v1/export/excel', 'alems.xlsx', 'Excel دانلود شد 📊')}>
                📊 Excel
              </button>
              <button className="btn-secondary text-xs"
                      onClick={() => download('/api/v1/export/json', 'alems.json', 'JSON کامل دانلود شد 💾')}>
                💾 JSON کامل
              </button>
            </div>
          </div>

          {/* پشتیبان‌گیری */}
          <div className="card">
            <h2 className="font-bold text-slate-900 mb-2">پشتیبان‌گیری و بازگردانی</h2>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              پشتیبان شامل کل پایگاه داده است؛ برای انتقال بین دستگاه‌ها فایل را دانلود کن.
            </p>
            <div className="flex gap-2 items-center mb-4">
              <input className="input !w-40 text-xs" dir="ltr" type="password"
                     placeholder="رمز (اختیاری)" value={backupPassword}
                     onChange={(e) => setBackupPassword(e.target.value)} />
              <button className="btn-primary text-xs" disabled={createBackup.isPending}
                      onClick={() => createBackup.mutate(!!backupPassword)}>
                💾 پشتیبان جدید
              </button>
            </div>
            {(backups?.data ?? []).length === 0 ? (
              <p className="text-sm text-slate-400">هنوز پشتیبانی ساخته نشده.</p>
            ) : (
              <div className="space-y-2">
                {(backups?.data ?? []).map((b) => (
                  <div key={b.id} className="flex items-center gap-2 rounded-xl border border-slate-100 px-3 py-2 text-xs">
                    <span className="flex-1 truncate">
                      {b.filename} {b.encrypted && '🔒'}
                      <span className="text-slate-400"> · {faNumber(Math.round(b.size_bytes / 1024))} کیلوبایت</span>
                    </span>
                    <span className="text-slate-400">{timeAgo(b.created_at)}</span>
                    <button className="btn-secondary !py-1 text-[10px]"
                            onClick={() => download(`/api/v1/backup/download/${b.id}`, b.filename, 'پشتیبان دانلود شد')}>
                      دانلود
                    </button>
                    <ConfirmButton className="btn-danger !py-1 text-[10px]"
                                   confirmText="مطمئنی؟ کل داده جایگزین می‌شود"
                                   onConfirm={() => restore.mutate(b.id)}>
                      بازگردانی
                    </ConfirmButton>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// state موقت سیاست‌ها
let policyLocalState: Record<string, unknown> = {};
function setPolicyLocal(patch: Record<string, unknown>) {
  policyLocalState = { ...policyLocalState, ...patch };
}

function PolicySave({ localState, onSave }: {
  localState: Record<string, unknown>;
  onSave: (payload: Record<string, unknown>) => void;
}) {
  const hasChanges = Object.keys(localState).length > 0;
  const payload: Record<string, unknown> = {};
  if ('wrong_penalty' in localState) payload.scoring_policy = { wrong_penalty: localState.wrong_penalty };
  if ('include_blank' in localState || 'intervals' in localState) {
    payload.review_policy = {
      ...(localState.include_blank !== undefined ? { include_blank: localState.include_blank } : {}),
      ...(localState.intervals !== undefined ? { intervals_days: localState.intervals } : {}),
    };
  }
  if ('max_questions' in localState) payload.exam_policy = { max_questions: localState.max_questions };
  if (!hasChanges) return null;
  return (
    <button className="btn-primary mt-3 text-xs"
            onClick={() => { onSave(payload); policyLocalState = {}; }}>
      ذخیره تنظیمات
    </button>
  );
}
