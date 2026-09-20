/**
 * Settings — حساب کاربری (phase 1: پروفایل + خروج) + تنظیمات آینده (فاز بعدی).
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../app/auth'
import { Page } from '../../components/Page'
import { Card } from '../../components/Card'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'

export function SettingsPage() {
  const { user, student, logout } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  const doLogout = async () => {
    setBusy(true)
    try {
      await logout()
      navigate('/auth', { replace: true })
    } finally {
      setBusy(false)
    }
  }

  const initials = (user?.full_name || user?.email || '?')
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')

  return (
    <Page title="تنظیمات" subtitle="حساب کاربری و تنظیمات ALEMS">
      <Card className="p-4 md:p-5">
        <h2 className="mb-4 text-title-sm font-bold">حساب کاربری</h2>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-primary-soft text-title font-bold text-primary">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-body font-semibold">{user?.full_name || 'کاربر'}</p>
            <p className="truncate text-body-sm text-muted" dir="ltr" style={{ textAlign: 'right' }}>
              {user?.email}
            </p>
            <p className="mt-1 text-body-sm text-muted">
              {student ? (
                <>
                  پایه: <strong className="text-ink">{student.grade ?? '—'}</strong> · رشته:{' '}
                  <strong className="text-ink">{student.track ?? '—'}</strong>
                  {student.target && (
                    <>
                      {' '}
                      · هدف: <strong className="text-ink">{student.target}</strong>
                    </>
                  )}
                </>
              ) : (
                <button onClick={() => navigate('/onboarding')} className="font-semibold text-primary">
                  پروفایل کنکوری را کامل کن
                </button>
              )}
            </p>
          </div>
          <Button variant="danger" onClick={doLogout} disabled={busy} ariaLabel="خروج از حساب">
            {busy ? <Spinner size={14} /> : null}
            خروج
          </Button>
        </div>
      </Card>

      <Card className="mt-4 p-2">
        <EmptyState
          icon="settings"
          text="تنظیمات بیشتر در فاز بعدی — زمان‌بندی (Asia/Tehran) و زبان (فارسی) از قبل فعال‌اند. گزینه‌های باز: حالت تیره، یادآوری check-in و…"
        />
      </Card>
    </Page>
  )
}
