/**
 * Dates — jalaali-js + dayjs (doc 03 §3.2 stack), week شنبه–جمعه (doc 03 §3.5).
 * Same Borkowski algorithm as backend core/jalali.py, so UI and API always agree.
 */
import { toJalaali, toGregorian, isLeapJalaaliYear } from 'jalaali-js'
import dayjs from 'dayjs'
import updateLocale from 'dayjs/plugin/updateLocale'
import 'dayjs/locale/fa'

// هفته شنبه تا جمعه (doc 03 §3.5)
dayjs.extend(updateLocale)
dayjs.updateLocale('fa', { weekStart: 0 })
dayjs.locale('fa')

export const JALALI_MONTHS_FA = [
  'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
  'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]

export const WEEKDAYS_FA = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']

export interface JalaliDate {
  jy: number
  jm: number
  jd: number
}

/** Today's Jalali date (browser local time = Tehran for the target user). */
export function todayJalali(date = new Date()): JalaliDate {
  return toJalaali(date.getFullYear(), date.getMonth() + 1, date.getDate())
}

/** 1405/07/29 */
export function formatJalali(j: JalaliDate): string {
  const p = (n: number, w = 2) => String(n).padStart(w, '0')
  return `${p(j.jy, 4)}/${p(j.jm)}/${p(j.jd)}`
}

/** «۲۹ شهریور ۱۴۵» */
export function formatJalaliLong(j: JalaliDate): string {
  return `${faDigits(String(j.jd))} ${JALALI_MONTHS_FA[j.jm - 1]} ${faDigits(String(j.jy))}`
}

/** 0=Saturday … 6=Friday for a Jalali date (doc 03 §3.5). */
export function jalaliWeekday(j: JalaliDate): number {
  const g = toGregorian(j.jy, j.jm, j.jd)
  const d = dayjs(new Date(g.gy, g.gm - 1, g.gd))
  // dayjs: 0=Sun..6=Sat → 0=Sat..6=Fri
  return (d.day() + 1) % 7
}

export function weekdayFa(j: JalaliDate): string {
  return WEEKDAYS_FA[jalaliWeekday(j)]
}

/** Saturday of the week containing the Jalali date. */
export function weekStart(j: JalaliDate): JalaliDate {
  const g = toGregorian(j.jy, j.jm, j.jd)
  const d = dayjs(new Date(g.gy, g.gm - 1, g.gd)).subtract(jalaliWeekday(j), 'day')
  return toJalaali(d.year(), d.month() + 1, d.date())
}

export function jalaliMonthDays(jy: number, jm: number): number {
  if (jm <= 6) return 31
  if (jm <= 11) return 30
  return isLeapJalaaliYear(jy) ? 30 : 29
}

/** Latin → Persian digits. */
export function faDigits(s: string): string {
  return s.replace(/[0-9]/g, (c) => String.fromCharCode(0x06f0 + Number(c)))
}
