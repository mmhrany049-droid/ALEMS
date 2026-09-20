/**
 * API client — envelope from doc 06:
 * { success, data, error: {code, message, details} | null, meta }
 * Persian-friendly: surfaces the backend's Persian `error.message`.
 *
 * Base is /api/v1 via the Vite proxy → http://127.0.0.1:8010 (doc 03 §3.2).
 * Auth: Bearer token from lib/auth (phase 1).
 */
import { clearToken, getStoredToken } from './auth'

export interface Envelope<T> {
  success: boolean
  data: T | null
  error: { code: string; message: string; details: Record<string, unknown> } | null
  meta: Record<string, unknown>
}

export class ApiError extends Error {
  code: string
  details: Record<string, unknown>
  status: number
  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken()
  const res = await fetch(`/api/v1${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  const body = (await res.json().catch(() => null)) as Envelope<T> | null
  if (!body) throw new ApiError(res.status, 'NETWORK', 'اتصال به سرور برقرار نشد.')
  if (!body.success) {
    if (res.status === 401) clearToken() // نشست منقضی — استراتژی ساده
    throw new ApiError(
      res.status,
      body.error?.code ?? 'UNKNOWN',
      body.error?.message ?? 'خطای نامشخص.',
      body.error?.details ?? {},
    )
  }
  return body.data as T
}

/** دانلود باینری با احراز هویت (export excel/pdf) — filename از Content-Disposition */
export async function apiBlob(path: string): Promise<{ blob: Blob; filename: string }> {
  const token = getStoredToken()
  const res = await fetch(`/api/v1${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  const ct = res.headers.get('content-type') ?? ''
  if (!res.ok || ct.includes('application/json')) {
    const body = (await res.json().catch(() => null)) as Envelope<unknown> | null
    if (res.status === 401) clearToken()
    throw new ApiError(
      res.status,
      body?.error?.code ?? 'DOWNLOAD_FAILED',
      body?.error?.message ?? 'دانلود ناموفق بود.',
      body?.error?.details ?? {},
    )
  }
  const cd = res.headers.get('content-disposition') ?? ''
  const m = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(cd)
  const filename = m ? decodeURIComponent(m[1]) : 'download'
  return { blob: await res.blob(), filename }
}

export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 4000)
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, data?: unknown) =>
    apiFetch<T>(path, { method: 'POST', body: data === undefined ? undefined : JSON.stringify(data) }),
  put: <T>(path: string, data?: unknown) =>
    apiFetch<T>(path, { method: 'PUT', body: data === undefined ? undefined : JSON.stringify(data) }),
  del: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
}
