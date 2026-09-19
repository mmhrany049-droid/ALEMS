// آغازکار — تکمیل پروفایل پیش از استفاده از بخش‌های اصلی (سند 08 §8.6)
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage, put } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../components/Toast';
import { FIELDS, GRADES } from '../../types';
import { toFaDigits } from '../../lib/jalali';

export default function OnboardingPage() {
  const { profile, refresh, logout } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    full_name: profile?.full_name ?? '',
    grade: profile?.grade && GRADES.includes(profile.grade) ? profile.grade : '',
    field: profile?.field && FIELDS.includes(profile.field) ? profile.field : '',
    academic_year: profile?.academic_year ?? '',
    target_rank: profile?.target_rank?.toString() ?? '',
    target_major: profile?.target_major ?? '',
  });

  const canSave = form.full_name.trim().length >= 2 && form.grade && form.field;

  const save = async () => {
    setError('');
    setBusy(true);
    try {
      await put('/students/me', {
        full_name: form.full_name.trim(),
        grade: form.grade,
        field: form.field,
        academic_year: form.academic_year || undefined,
        target_rank: form.target_rank ? Number(form.target_rank) : undefined,
        target_major: form.target_major || undefined,
      });
      await refresh();
      toast.show('پروفایل تکمیل شد — مسیر کنکورت شروع شد! 🚀');
      navigate('/today');
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-bl from-primary-50 to-slate-100">
      <div className="w-full max-w-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="size-9 rounded-xl bg-primary-600 text-white grid place-items-center font-bold">A</div>
            <div>
              <div className="font-bold text-slate-900 text-sm">خوش آمدی!</div>
              <div className="text-xs text-slate-400">قبل از شروع، پروفایلت را تکمیل کن</div>
            </div>
          </div>
          <button className="btn-secondary !py-1.5 text-xs" onClick={logout}>
            خروج از حساب
          </button>
        </div>

        <div className="card">
          {/* نوار مرحله */}
          <div className="flex items-center gap-2 mb-6">
            <span className="flex-1 h-1.5 rounded-full bg-primary-600" />
            <span className="chip bg-primary-50 text-primary-700">مرحله ۱ از ۱ — پروفایل</span>
          </div>

          <div className="space-y-5">
            <div>
              <label className="label">نام کامل *</label>
              <input className="input" value={form.full_name}
                     onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                     placeholder="مثلاً: علی محمدی" autoFocus />
            </div>

            <div>
              <label className="label">پایه تحصیلی *</label>
              <div className="flex flex-wrap gap-1.5">
                {GRADES.map((g) => (
                  <button key={g}
                    className={`chip border cursor-pointer !px-3 !py-1.5 ${form.grade === g ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-slate-600 border-slate-200 hover:border-primary-300'}`}
                    onClick={() => setForm((f) => ({ ...f, grade: g }))}>
                    {g}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">رشته *</label>
              <div className="flex flex-wrap gap-1.5">
                {FIELDS.map((f) => (
                  <button key={f}
                    className={`chip border cursor-pointer !px-3 !py-1.5 ${form.field === f ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-slate-600 border-slate-200 hover:border-primary-300'}`}
                    onClick={() => setForm((x) => ({ ...x, field: f }))}>
                    {f}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5">
                درخت دروس و کتاب‌ها بر اساس پایه و رشته‌ات فیلتر می‌شود.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">سال تحصیلی</label>
                <input className="input" value={form.academic_year}
                       onChange={(e) => setForm((f) => ({ ...f, academic_year: e.target.value }))}
                       placeholder="۱۴۰۴-۱۴۰۵" />
              </div>
              <div>
                <label className="label">رتبه هدف</label>
                <input className="input" dir="ltr" type="number" min={1}
                       value={form.target_rank}
                       onChange={(e) => setForm((f) => ({ ...f, target_rank: e.target.value }))}
                       placeholder="مثلاً ۱۰۰۰" />
              </div>
            </div>

            <div>
              <label className="label">رشته دانشگاهی هدف</label>
              <input className="input" value={form.target_major}
                     onChange={(e) => setForm((f) => ({ ...f, target_major: e.target.value }))}
                     placeholder="مثلاً مهندسی کامپیوتر" />
            </div>

            {error && (
              <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
                {error}
              </div>
            )}

            <button className="btn-primary w-full !py-3" disabled={!canSave || busy} onClick={save}>
              {busy ? 'در حال ذخیره...' : canSave ? 'شروع کن 🚀' : 'نام، پایه و رشته را انتخاب کن'}
            </button>
            <p className="text-[11px] text-slate-400 text-center leading-relaxed">
              فقط ۳ فیلد ستاره‌دار الزامی است؛ بعداً از تنظیمات هم می‌توانی تغییرش دهی.
              بعد از تکمیل، اولین کار ثبت <strong>وضعیت روزانه</strong> (انرژی ۱ تا {toFaDigits(5)}) در صفحه «امروز» است.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
