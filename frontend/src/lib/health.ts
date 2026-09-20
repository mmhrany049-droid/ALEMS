/** Backend health — GET /health (root, proxied by Vite to 127.0.0.1:8010). */
export interface HealthData {
  status: string
  app: string
  version: string
  app_version: string
  schema_version: string
  alembic_revision: string
  db: { type: string }
  now_utc: string
  now_tehran: string
  today_jalali: string
  today_jalali_fa: string
  week_start: string
  timezone: string
}

export async function fetchHealth(): Promise<HealthData> {
  const res = await fetch('/health')
  if (!res.ok) throw new Error(`backend ${res.status}`)
  const body = (await res.json()) as { success: boolean; data: HealthData | null; error: unknown }
  if (!body.success || !body.data) throw new Error('bad envelope')
  return body.data
}
