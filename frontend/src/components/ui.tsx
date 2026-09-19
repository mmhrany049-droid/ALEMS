// کامپوننت‌های مشترک UI
import { ReactNode, useState } from 'react';

export function PageHeader({ title, subtitle, actions }: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

export function EmptyState({ icon = '📝', title, description, action }: {
  icon?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center justify-center text-center py-12 gap-3">
      <div className="text-4xl">{icon}</div>
      <h3 className="font-bold text-slate-800">{title}</h3>
      {description && <p className="text-sm text-slate-500 max-w-sm">{description}</p>}
      {action}
    </div>
  );
}

export function Spinner({ label = 'در حال بارگذاری...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-slate-500">
      <span className="inline-block size-6 border-3 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function StatCard({ label, value, hint, accent = 'bg-primary-600' }: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: string;
}) {
  return (
    <div className="card flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <span className={`inline-block size-2.5 rounded-full ${accent}`} />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      {hint && <div className="text-xs text-slate-400">{hint}</div>}
    </div>
  );
}

export function Modal({ open, onClose, title, children, wide }: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  wide?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/50" onClick={onClose} />
      <div className={`relative bg-white rounded-2xl shadow-xl w-full ${wide ? 'max-w-3xl' : 'max-w-lg'} max-h-[90vh] overflow-y-auto`}>
        <div className="sticky top-0 bg-white border-b border-slate-100 px-5 py-4 flex items-center justify-between">
          <h2 className="font-bold text-slate-900">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-xl leading-none" aria-label="بستن">
            ✕
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export function Chip({ children, color = 'bg-slate-100 text-slate-700' }: {
  children: ReactNode;
  color?: string;
}) {
  return <span className={`chip ${color}`}>{children}</span>;
}

/** نوار درصد با رنگ معنادار */
export function PercentBar({ value, negative = false }: { value: number | null; negative?: boolean }) {
  if (value === null || value === undefined) return <span className="text-slate-400 text-sm">—</span>;
  const clamped = Math.max(0, Math.min(100, value));
  const color = negative || value < 0
    ? 'bg-red-500'
    : value >= 70 ? 'bg-emerald-500' : value >= 40 ? 'bg-amber-500' : 'bg-orange-500';
  return (
    <div className="flex items-center gap-2 min-w-28">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${clamped}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-700 tabular-nums">
        {value < 0 ? 'منفی' : ''}
        {Math.round(value * 100) / 100}٪
      </span>
    </div>
  );
}

/** تأیید دومرحله‌ای عملیات مخرب (۷.۹) */
export function ConfirmButton({ onConfirm, children, className = 'btn-danger', confirmText = 'مطمئنی؟ دوباره کلیک کن' }: {
  onConfirm: () => void;
  children: ReactNode;
  className?: string;
  confirmText?: string;
}) {
  const [armed, setArmed] = useState(false);
  return (
    <button
      className={className}
      onClick={() => {
        if (armed) {
          setArmed(false);
          onConfirm();
        } else {
          setArmed(true);
          setTimeout(() => setArmed(false), 4000);
        }
      }}
    >
      {armed ? confirmText : children}
    </button>
  );
}
