/**
 * ALEMS 2.0 — Motion System (doc 07.4, Framer Motion اجباری).
 * Durations from tokens: fast 180 / normal 280 / slow 400 (ms).
 * Easing: easeOut for entrance, easeInOut for movement (doc 03 §3.7).
 *
 * Reduced motion (doc 07.4/NFR-5): <MotionConfig reducedMotion="user"> is set
 * in App; with it, transform animations become opacity-only for users who
 * prefer reduced motion.
 */
import type { Variants } from 'framer-motion'

export const D = {
  fast: 0.18,
  normal: 0.28,
  slow: 0.4,
} as const

export const EASE_OUT = [0.16, 1, 0.3, 1] as const
export const EASE_IN_OUT = [0.45, 0, 0.55, 1] as const

/** 1) Page transition: fade + slide جزئی (8–12px) */
export const page: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: D.normal, ease: EASE_OUT } },
  exit: { opacity: 0, y: -8, transition: { duration: D.fast, ease: EASE_IN_OUT } },
}
/** alias — phase-0 spec name */
export const pageVariants = page

/** 2) List stagger: صف مرور/برنامه — تأخیر ۳۰–۴۰ms */
export const staggerList: Variants = {
  initial: {},
  animate: { transition: { staggerChildren: 0.035, delayChildren: 0.04 } },
}

export const listItem: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: D.normal, ease: EASE_OUT } },
}
/** alias — phase-0 spec name */
export const listItemVariants = listItem

/** fadeInUp — ورود ملایم بالا-به-پایین (doc 07.4) */
export const fadeInUp: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: D.normal, ease: EASE_OUT } },
  exit: { opacity: 0, transition: { duration: D.fast } },
}

/** 5) Today Hub mount: cascade ورود بلوک‌ها */
export const todayCascade: Variants = {
  initial: {},
  animate: { transition: { staggerChildren: 0.05, delayChildren: 0.05 } },
}

export const todayBlock: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: D.normal, ease: EASE_OUT } },
}

/** 3) Success pulse: ثبت تست درست — تیک سبز کوتاه */
export const successPulse: Variants = {
  initial: { scale: 0.6, opacity: 0 },
  animate: {
    scale: [0.6, 1.15, 1],
    opacity: [0, 1, 1],
    transition: { duration: D.slow, ease: EASE_OUT, times: [0, 0.6, 1] },
  },
  exit: { opacity: 0, transition: { duration: D.fast } },
}

/** 4) Progress bar: نرم (پوشش هفتگی) */
export const progressFill = {
  initial: { scaleX: 0 },
  animate: { scaleX: 1, transition: { duration: D.slow, ease: EASE_IN_OUT } },
}

/** 6) Modal/sheet: scale + fade */
export const modal: Variants = {
  initial: { opacity: 0, scale: 0.96, y: 8 },
  animate: { opacity: 1, scale: 1, y: 0, transition: { duration: D.fast, ease: EASE_OUT } },
  exit: { opacity: 0, scale: 0.97, transition: { duration: D.fast } },
}

export const backdrop = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: D.fast } },
  exit: { opacity: 0, transition: { duration: D.fast } },
}

/** 7) Button press: scale 0.98 */
export const buttonTap = {
  initial: { scale: 1 },
  whileTap: { scale: 0.98 },
  transition: { duration: D.fast, ease: EASE_IN_OUT },
}

/** 8) Planner build: مراحل معنادار (تحلیل → ظرفیت → تخصیص → آماده) */
export const plannerStep: Variants = {
  initial: { opacity: 0, x: 14 },
  animate: (i: number = 0) => ({
    opacity: 1,
    x: 0,
    transition: { delay: 0.25 + i * 0.45, duration: D.normal, ease: EASE_OUT },
  }),
  exit: { opacity: 0, transition: { duration: D.fast } },
}

/** Generic fade (reduced-motion-safe) */
export const fade: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: D.normal, ease: EASE_OUT } },
  exit: { opacity: 0, transition: { duration: D.fast } },
}
