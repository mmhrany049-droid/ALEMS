// کلاینت API — پاکت استاندارد {success, data, error, meta} و توکن JWT
import axios from 'axios';

const TOKEN_KEY = 'alems_token';

export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
  if (token) api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  else delete api.defaults.headers.common['Authorization'];
}

// توکن ذخیره‌شده در شروع برنامه
if (getToken()) {
  api.defaults.headers.common['Authorization'] = `Bearer ${getToken()}`;
}

export interface ApiEnvelope<T = unknown> {
  success: boolean;
  data: T;
  error: null | { code: string; message: string; details?: Record<string, unknown> };
  meta?: Record<string, unknown>;
}

/** پیام خطای فارسی برای نمایش به کاربر */
export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const body = err.response?.data as ApiEnvelope | undefined;
    if (body?.error?.message) return body.error.message;
    if (err.response?.status === 401) return 'نشست شما منقضی شده است. دوباره وارد شوید.';
    if (err.response?.status === 404) return 'مورد درخواستی یافت نشد.';
    if (err.response && err.response.status >= 500) return 'خطای سرور. لطفاً دوباره تلاش کنید.';
    return 'خطا در ارتباط با سرور. اتصال خود را بررسی کنید.';
  }
  return 'خطای نامشخص رخ داد.';
}

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<ApiEnvelope<T>> {
  const r = await api.get<ApiEnvelope<T>>(url, { params });
  return r.data;
}

export async function post<T>(url: string, body?: unknown, params?: Record<string, unknown>): Promise<ApiEnvelope<T>> {
  const r = await api.post<ApiEnvelope<T>>(url, body, { params });
  return r.data;
}

export async function put<T>(url: string, body?: unknown): Promise<ApiEnvelope<T>> {
  const r = await api.put<ApiEnvelope<T>>(url, body);
  return r.data;
}

export async function del<T>(url: string): Promise<ApiEnvelope<T>> {
  const r = await api.delete<ApiEnvelope<T>>(url);
  return r.data;
}

/** دانلود فایل (PDF/Excel/JSON/Backup) با توکن */
export async function downloadFile(url: string, fallbackName: string): Promise<void> {
  const r = await api.get(url, { responseType: 'blob' });
  const dispo = r.headers['content-disposition'] as string | undefined;
  const match = dispo?.match(/filename="?([^";]+)"?/);
  const name = match?.[1] ?? fallbackName;
  const blobUrl = URL.createObjectURL(r.data as Blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(blobUrl);
}
