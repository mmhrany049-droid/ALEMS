/** Page — page transition wrapper (doc 07.4 #1: fade + slide 8–12px). */
import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { page } from '../motion/variants'

export function Page({ title, subtitle, children }: { title?: string; subtitle?: string; children: ReactNode }) {
  return (
    <motion.div variants={page} initial="initial" animate="animate" exit="exit" className="mx-auto w-full max-w-5xl px-4 py-5 pb-24 md:px-5 md:py-6 md:pb-8">
      {title && (
        <header className="mb-5">
          <h1 className="text-title font-bold">{title}</h1>
          {subtitle && <p className="mt-1 text-body-sm text-muted">{subtitle}</p>}
        </header>
      )}
      {children}
    </motion.div>
  )
}
