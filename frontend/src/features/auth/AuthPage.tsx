// ورود و ثبت‌نام — پیام‌های خطا فارسی (AT-03)
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { post, errorMessage } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../components/Toast';

interface TokenResponse {
  access_token: string;
  user: { username: string };
}

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (mode === 'register') {
        await post('/auth/register', { username, password, full_name: fullName || undefined });
      }
      const r = await post<TokenResponse>('/auth/login', { username, password });
      await login(r.data.access_token);
      toast.show(mode === 'register' ? 'حساب شما ساخته شد. خوش آمدید! 🎉' : 'خوش آمدید! 👋');
      navigate('/today');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* ستون معرفی */}
      <div className="hidden lg:flex flex-col justify-center bg-gradient-to-bl from-primary-700 to-primary-900 text-white p-12">
        <div className="flex items-center gap-3 mb-8">
          <div className="size-14 rounded-2xl bg-white/15 grid place-items-center text-2xl font-bold">A</div>
          <div>
            <div className="text-2xl font-bold">ALEMS</div>
            <div className="text-white/70 text-sm">سامانه مدیریت زندگی تحصیلی و مسیر کنکور</div>
          </div>
        </div>
        <h1 className="text-3xl font-bold leading-relaxed mb-4">
          مسیر کنکورت را هوشمندانه مدیریت کن
        </h1>
        <ul className="space-y-3 text-white/85 text-sm leading-relaxed">
          <li>✅ ثبت مطالعه، تست و غلط‌ها در یک‌جا</li>
          <li>✅ صف مرور خودکار بر اساس غلط‌ها و تیک‌ها</li>
          <li>✅ برنامه هفتگی واقع‌بینانه با تقویم شمسی</li>
          <li>✅ درصد کنکوری و تحلیل عملکرد</li>
          <li>✅ آفلاین‌محور — داده‌ها متعلق به خودت است</li>
        </ul>
      </div>

      {/* ستون فرم */}
      <div className="flex items-center justify-center p-6">
        <div className="card w-full max-w-md">
          <div className="flex gap-2 mb-6 bg-slate-100 rounded-xl p-1">
            <button
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
                mode === 'login' ? 'bg-white shadow text-primary-700' : 'text-slate-500'
              }`}
              onClick={() => { setMode('login'); setError(''); }}
            >
              ورود
            </button>
            <button
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
                mode === 'register' ? 'bg-white shadow text-primary-700' : 'text-slate-500'
              }`}
              onClick={() => { setMode('register'); setError(''); }}
            >
              ثبت‌نام
            </button>
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="label" htmlFor="fullName">نام کامل (اختیاری)</label>
                <input id="fullName" className="input" value={fullName}
                       onChange={(e) => setFullName(e.target.value)}
                       placeholder="مثلاً: علی محمدی" />
              </div>
            )}
            <div>
              <label className="label" htmlFor="username">نام کاربری</label>
              <input id="username" className="input" dir="ltr" required value={username}
                     onChange={(e) => setUsername(e.target.value)}
                     placeholder="username" autoComplete="username" />
            </div>
            <div>
              <label className="label" htmlFor="password">رمز عبور</label>
              <input id="password" className="input" dir="ltr" required type="password"
                     value={password} onChange={(e) => setPassword(e.target.value)}
                     placeholder="حداقل ۶ کاراکتر" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
            </div>

            {error && (
              <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
                {error}
              </div>
            )}

            <button className="btn-primary w-full !py-2.5" disabled={busy}>
              {busy ? 'لطفاً صبر کنید...' : mode === 'login' ? 'ورود به حساب' : 'ساخت حساب جدید'}
            </button>
          </form>

          <p className="text-xs text-slate-400 text-center mt-4 leading-relaxed">
            چند پروفایل می‌توانی روی این دستگاه بسازی؛ داده‌های هر نفر جدا ذخیره می‌شود.
          </p>
        </div>
      </div>
    </div>
  );
}
