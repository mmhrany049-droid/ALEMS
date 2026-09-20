/**
 * Settings — phase 0: theme (dark/light first-class, doc 07.2) + about.
 * Policy settings (k، چرخه مرور، …) از فاز ۱ (GET/PUT /settings) می‌رسند.
 */
import { useQuery } from '@tanstack/react-query'
import { Card } from '../../components/Card'
import { Icon } from '../../components/Icon'
import { Page } from '../../components/Page'
import { useTheme } from '../../app/theme'
import { fetchHealth } from '../../lib/health'
import { todayJalali, formatJalali, weekdayFa, formatJalaliLong } from '../../lib/dates'
import { faDigits } from '../../lib/dates'
import { fade } from '../../motion/variants'
import { motion } from 'framer-motion'

export function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: fetchHealth, staleTime: 60_000 })
  const t = todayJalali()

  return (
    <Page title="تنظیمات" subtitle="ظاهر و اطلاعات سامانه">
      <div className="flex flex-col gap-4">
        {/* theme */}
        <motion.div variants={fade} initial="initial" animate="animate">
          <Card className="p-4 md:p-5">
            <h2 className="text-title-sm font-bold">حالت نمایش</h2>
            <p className="mt-1 text-body-sm text-muted">تاریک و روشن هر دو درجه یک‌اند (doc 07.2).</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {(
                [
                  ['light', 'روشن', 'sun'],
                  ['dark', 'تاریک', 'moon'],
                ] as const
              ).map(([value, label, icon]) => (
                <button
                  key={value}
                  onClick={() => setTheme(value)}
                  aria-pressed={theme === value}
                  className={[
                    'flex flex-col items-center gap-2 rounded-md border px-4 py-4 text-body-sm font-semibold transition-all',
                    theme === value
                      ? 'border-primary bg-primary-soft text-primary'
                      : 'border-border bg-surface text-muted hover:bg-surface-2',
                  ].join(' ')}
                >
                  <Icon name={icon} size={22} />
                  {label}
                </button>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* about */}
        <Card className="p-4 md:p-5">
          <h2 className="text-title-sm font-bold">درباره سامانه</h2>
          <dl className="mt-4 grid grid-cols-1 gap-x-6 gap-y-3 text-body-sm sm:grid-cols-2">
            <Row k="نسخه محصول" v={health ? faDigits(health.app_version) : '—'} />
            <Row k="نسخه schema" v={health ? faDigits(health.schema_version) : '—'} />
            <Row k="پایگاه داده" v={health ? health.db.type : '—'} />
            <Row k="پورت backend" v={faDigits('8010')} />
            <Row k="پورت frontend" v={faDigits('5173')} />
            <Row k="هفته" v="شنبه تا جمعه" />
            <Row k="timezone" v="Asia/Tehran" />
            <Row k="امروز (شمسی)" v={`${formatJalali(t)} — ${weekdayFa(t)}`} />
          </dl>
          {health && (
            <p className="mt-4 rounded-md bg-surface-2 px-3 py-2 text-body-sm text-muted">
              {formatJalaliLong(t)} · backend متصل (rev {health.alembic_revision})
            </p>
          )}
        </Card>
      </div>
    </Page>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border pb-2">
      <dt className="text-muted">{k}</dt>
      <dd className="font-semibold">{v}</dd>
    </div>
  )
}
