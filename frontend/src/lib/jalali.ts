// ابزارهای تقویم جلالی — jalaali-js + dayjs
// هفته از شنبه شروع می‌شود؛ منطقه زمانی Asia/Tehran
import jalaali from 'jalaali-js';
import dayjs from 'dayjs';

export const JALALI_MONTHS = [
  'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
  'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
];

export const WEEKDAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'];
export const WEEKDAYS_SHORT = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];

const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹';

/** تبدیل ارقام لاتین به فارسی */
export function toFaDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)]);
}

/** شماره روز هفته ایرانی: ۰=شنبه ... ۶=جمعه */
export function jalaliWeekday(date: Date): number {
  return (date.getDay() + 1) % 7;
}

/** تبدیل تاریخ میلادی به جلالی */
export function toJalali(date: Date): { jy: number; jm: number; jd: number } {
  return jalaali.toJalaali(date.getFullYear(), date.getMonth() + 1, date.getDate());
}

/** تبدیل جلالی به میلادی */
export function toGregorian(jy: number, jm: number, jd: number): Date {
  const g = jalaali.toGregorian(jy, jm, jd);
  return new Date(g.gy, g.gm - 1, g.gd);
}

/** قالب ۱۴۰۴/۰۶/۲۸ */
export function formatJalali(iso: string | Date | undefined | null): string {
  if (!iso) return '—';
  const date = typeof iso === 'string' ? new Date(iso.length <= 10 ? iso + 'T00:00:00' : iso) : iso;
  const { jy, jm, jd } = toJalali(date);
  return toFaDigits(`${jy}/${String(jm).padStart(2, '0')}/${String(jd).padStart(2, '0')}`);
}

/** قالب بلند: ۲۸ شهریور ۱۴۰۵ */
export function formatJalaliLong(iso: string | Date | undefined | null): string {
  if (!iso) return '—';
  const date = typeof iso === 'string' ? new Date(iso.length <= 10 ? iso + 'T00:00:00' : iso) : iso;
  const { jy, jm, jd } = toJalali(date);
  return toFaDigits(`${jd}`) + ' ' + JALALI_MONTHS[jm - 1] + ' ' + toFaDigits(jy);
}

/** نام روز هفته: شنبه ۲۸ شهریور */
export function formatJalaliWithWeekday(iso: string | Date): string {
  const date = typeof iso === 'string' ? new Date(iso.length <= 10 ? iso + 'T00:00:00' : iso) : iso;
  return `${WEEKDAYS[jalaliWeekday(date)]} ${formatJalaliLong(date)}`;
}

/** شنبه‌ی هفته‌ی تاریخ داده‌شده (ISO) */
export function weekStartISO(date: Date = new Date()): string {
  const d = new Date(date);
  d.setDate(d.getDate() - jalaliWeekday(d));
  return dayjs(d).format('YYYY-MM-DD');
}

/** روزهای هفته ایرانی از شنبه تا جمعه (ISO) */
export function weekDaysISO(weekStart: string): string[] {
  const start = dayjs(weekStart);
  return Array.from({ length: 7 }, (_, i) => start.add(i, 'day').format('YYYY-MM-DD'));
}

/** تاریخ امروز به وقت تهران (ISO) */
export function todayISO(): string {
  // تهران UTC+3:30
  const now = new Date();
  const tehran = new Date(now.getTime() + (3.5 * 60 + now.getTimezoneOffset()) * 60000);
  return dayjs(tehran).format('YYYY-MM-DD');
}

/** زمان نسبی خوانا */
export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'همین حالا';
  if (minutes < 60) return `${toFaDigits(minutes)} دقیقه پیش`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${toFaDigits(hours)} ساعت پیش`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${toFaDigits(days)} روز پیش`;
  return formatJalaliLong(iso);
}

/** مدت به شکل خوانا: ۲ ساعت و ۳۰ دقیقه */
export function formatMinutes(minutes: number): string {
  if (!minutes) return '۰';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h && m) return `${toFaDigits(h)} ساعت و ${toFaDigits(m)} دقیقه`;
  if (h) return `${toFaDigits(h)} ساعت`;
  return `${toFaDigits(m)} دقیقه`;
}

/** عدد به فارسی با جداکننده */
export function faNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return toFaDigits(String(value));
}

/** درصد با یک رقم اعشار در صورت وجود */
export function faPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const rounded = Math.round(value * 100) / 100;
  return toFaDigits(String(rounded)) + '٪';
}
