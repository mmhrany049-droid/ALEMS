/**
 * ErrorBoundary — آخرین خط دفاعی UI (NFR-5: پیام فارسی؛ هیچ صفحه سفید مرگباری).
 * doc 07: خطای رندر هیچ صفحه‌ای نباید کل اپ را نابود کند.
 *
 * دو لایه استفاده:
 *  1. ریشه App: سقوط کامل (AuthProvider/Router) → fallback ایستاده با دکمه تلاش
 *     دوباره + لینک خانه (عمداً از Link استفاده نمی‌شود تا خارج از Router هم کار کند).
 *  2. داخل Layout با key=مسیر: خطای یک صفحه فقط همان صفحه را می‌گیرد و با تغییر
 *     مسیر، خودکار reset می‌شود (nav سالم می‌ماند).
 *
 * توجه: خطا قورت داده نمی‌شود — همیشه console.error کامل + fallback قابل دیدن.
 */
import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  /** عنوان فارسی fallback (پیش‌فرض: خطای غیرمنتظره در ALEMS) */
  title?: string
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ALEMS] render error:', error, info.componentStack)
  }

  retry = () => this.setState({ error: null })

  render() {
    const { error } = this.state
    if (!error) return this.props.children
    const title = this.props.title ?? 'خطای غیرمنتظره در ALEMS'
    return (
      <div
        role="alert"
        className="flex min-h-[240px] flex-col items-center justify-center gap-3 p-8 text-center"
      >
        <p className="text-heading-3 text-text">⚠️ {title}</p>
        <p className="max-w-md text-body-sm text-muted">
          این صفحه به مشکل خورد. جزئیات خطا در کنسول ثبت شد؛ می‌توانی دوباره تلاش کنی یا به
          صفحه امروز برگردی.
        </p>
        <div className="mt-1 flex items-center gap-2">
          <button
            type="button"
            onClick={this.retry}
            className="rounded-lg bg-primary px-4 py-2 text-body text-on-primary transition-colors hover:bg-primary-hover"
          >
            تلاش دوباره
          </button>
          <a
            href="/"
            className="rounded-lg border border-border px-4 py-2 text-body text-text transition-colors hover:bg-hover"
          >
            بازگشت به امروز
          </a>
        </div>
        <pre
          dir="ltr"
          className="mt-2 max-w-md overflow-x-auto whitespace-pre-wrap rounded-md bg-surface-2 p-3 text-left text-[11px] text-muted"
        >
          {error.message}
        </pre>
      </div>
    )
  }
}
