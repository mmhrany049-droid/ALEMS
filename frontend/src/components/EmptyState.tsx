/**
 * EmptyState — doc 07.8: هر صفحه خالی: تصویر/آیکون سبک + یک جمله + یک CTA واضح.
 */
import type { ReactNode } from 'react'
import { fade } from '../motion/variants'
import { motion } from 'framer-motion'
import { Icon, type IconName } from './Icon'

interface Props {
  icon: IconName
  text: string
  action?: ReactNode
}

export function EmptyState({ icon, text, action }: Props) {
  return (
    <motion.div variants={fade} initial="initial" animate="animate" className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border bg-surface/60 px-6 py-14 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-2 text-muted">
        <Icon name={icon} size={30} />
      </div>
      <p className="max-w-sm text-body text-muted">{text}</p>
      {action && <div className="mt-1">{action}</div>}
    </motion.div>
  )
}
