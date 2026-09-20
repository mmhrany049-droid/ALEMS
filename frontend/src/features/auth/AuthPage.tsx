/**
 * Auth — ورود/ثبت‌نام با Framer Motion (phase 1).
 * - جابه‌جایی login/register با slide + fade
 * - خطای فارسی backend با shake ملایم
 * - موفقیت: toast + ریدایرکت فوری توسط GuestOnly (بر اساس کامل بودن پروفایل
 *   به /onboarding یا /) — بدون setTimeout و بدون flash شدن صفحه Today.
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from '../../app/auth'
import { useToast } from '../../app/toast'
import { Spinner } from '../../components/Spinner'
import { D, EASE_OUT } from '../../motion/variants'

type Mode = 'login' | 'register'

export function AuthPage() {
  const { login, register } = useAuth()
  const toast = useToast()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    setError(null)
    setBusy(true)
    try {
      if (mode === 'login') {
        await login(email, password)
        toast.success('ورود موفق — خوش آمدی!')
      } else {
        await register(email, password, fullName.trim() || null)
        toast.success('حساب ساخته شد — بیا پروفایلت را کامل کنیم')
      }
      // ریدایرکت دستی اینجا انجام نمی‌شود: به محض ذخیره user، GuestOnly
      // کاربر را به مقصد درست می‌برد (پروفایل ناقص → onboarding).
    } catch (e) {
      setError(e instanceof Error ? e.message : 'خطایی پیش آمد؛ دوباره تلاش کنید.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-bg px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: D.normal, ease: EASE_OUT }}
        className="grid w-full max-w-4xl overflow-hidden rounded-lg border border-border bg-surface shadow-soft md:grid-cols-2"
      >
        {/* brand panel */}
        <div className="relative hidden flex-col justify-between bg-primary p-6 text-white md:flex">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-white/15">
              <svg width="20" height="20" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                <path d="M9 22 16 9l7 13" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="text-title font-bold">ALEMS 2.0</div>
          </div>
          <div>
            <h2 className="text-title-lg font-bold leading-relaxed">سیستم‌عامل شخصی کنکورت</h2>
            <p className="mt-3 text-body-sm leading-7 text-white/85">
              ثبت واقعیت مطالعه، سنجش درست، مرور هوشمند و برنامه‌ریزی واقع‌بینانه — با تقویم شمسی و
              هفته‌ی شنبه تا جمعه.
            </p>
          </div>
          <p className="text-body-sm text-white/70">Offline-first · داده‌ها مال خودت‌اند</p>
        </div>

        {/* form panel */}
        <div className="p-6 md:p-8">
          <div className="mb-6 flex items-center gap-2 md:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-white">
              <svg width="18" height="18" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                <path d="M9 22 16 9l7 13" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span className="text-title-sm font-bold">ALEMS 2.0</span>
          </div>

          {/* mode tabs */}
          <div className="mb-6 grid grid-cols-2 gap-1 rounded-md bg-surface-2 p-1">
            {(['login', 'register'] as const).map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m)
                  setError(null)
                }}
                className="relative rounded px-3 py-2 text-body-sm font-semibold"
                aria-pressed={mode === m}
              >
                {mode === m && (
                  <motion.span
                    layoutId="auth-tab"
                    className="absolute inset-0 rounded bg-surface shadow-soft"
                    transition={{ duration: D.fast, ease: EASE_OUT }}
                  />
                )}
                <span className={mode === m ? 'relative text-ink' : 'relative text-muted'}>
                  {m === 'login' ? 'ورود' : 'ثبت‌نام'}
                </span>
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.form
              key={mode}
              initial={{ opacity: 0, x: mode === 'login' ? -14 : 14 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mode === 'login' ? 14 : -14 }}
              transition={{ duration: D.fast, ease: EASE_OUT }}
              onSubmit={(e) => {
                e.preventDefault()
                submit()
              }}
              className="flex flex-col gap-4"
            >
              {mode === 'register' && (
                <Field label="نام و نام خانوادگی" value={fullName} onChange={setFullName} placeholder="مثلاً سارا محمدی" autoComplete="name" />
              )}
              <Field label="ایمیل" value={email} onChange={setEmail} placeholder="you@example.com" type="email" autoComplete="email" required dir="ltr" inputAlignRight />
              <Field label="رمز عبور" value={password} onChange={setPassword} placeholder="حداقل ۸ کاراکتر" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required dir="ltr" inputAlignRight />

              <AnimatePresence>
                {error && (
                  <motion.p
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="rounded-md bg-danger-soft px-3 py-2 text-body-sm text-danger"
                    role="alert"
                  >
                    {error}
                  </motion.p>
                )}
              </AnimatePresence>

              <motion.button
                type="submit"
                whileTap={{ scale: 0.98 }}
                transition={{ duration: D.fast }}
                disabled={busy}
                className="mt-1 flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-3 text-body font-semibold text-white shadow-soft transition-opacity hover:opacity-90 disabled:opacity-60"
              >
                {busy && <Spinner size={16} />}
                {mode === 'login' ? 'ورود به ALEMS' : 'ساخت حساب'}
              </motion.button>

              <p className="text-center text-body-sm text-muted">
                {mode === 'login' ? (
                  <>
                    حساب نداری؟{' '}
                    <button type="button" onClick={() => setMode('register')} className="font-semibold text-primary">
                      ثبت‌نام کن
                    </button>
                  </>
                ) : (
                  <>
                    قبلاً ثبت‌نام کرده‌ای؟{' '}
                    <button type="button" onClick={() => setMode('login')} className="font-semibold text-primary">
                      وارد شو
                    </button>
                  </>
                )}
              </p>
            </motion.form>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  required,
  autoComplete,
  dir,
  inputAlignRight,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  required?: boolean
  autoComplete?: string
  dir?: 'ltr' | 'rtl'
  inputAlignRight?: boolean
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-body-sm font-semibold">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        autoComplete={autoComplete}
        dir={dir}
        className={[
          'w-full rounded-md border border-border bg-surface px-3 py-2.5 text-body outline-none transition-colors',
          'focus:border-primary focus:ring-2 focus:ring-primary/25',
          dir === 'ltr' ? 'text-right' : inputAlignRight ? 'text-right' : '',
        ].join(' ')}
        style={dir === 'ltr' ? { textAlign: 'left' } : undefined}
      />
    </label>
  )
}
