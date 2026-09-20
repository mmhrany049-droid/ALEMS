/** Button — Framer Motion press (doc 07.4 #7: scale 0.98). `to` → navigates. */
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { buttonTap } from '../motion/variants'

type Variant = 'primary' | 'ghost' | 'soft' | 'danger'

const STYLES: Record<Variant, string> = {
  primary: 'bg-primary text-white hover:opacity-90 shadow-soft',
  ghost: 'bg-transparent text-ink border border-border hover:bg-surface-2',
  soft: 'bg-primary-soft text-primary hover:opacity-90',
  danger: 'bg-danger-soft text-danger hover:opacity-90',
}

interface Props {
  children: ReactNode
  onClick?: () => void
  to?: string
  variant?: Variant
  className?: string
  disabled?: boolean
  type?: 'button' | 'submit'
  ariaLabel?: string
}

export function Button({ children, onClick, to, variant = 'primary', className = '', disabled, type = 'button', ariaLabel }: Props) {
  const navigate = useNavigate()
  const handle = () => {
    if (to) navigate(to)
    onClick?.()
  }
  return (
    <motion.button
      type={type}
      whileTap={disabled ? undefined : buttonTap.whileTap}
      transition={buttonTap.transition}
      onClick={handle}
      disabled={disabled}
      aria-label={ariaLabel}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-md px-4 py-2.5',
        'text-body-sm font-semibold transition-opacity',
        'disabled:opacity-50 disabled:pointer-events-none',
        STYLES[variant],
        className,
      ].join(' ')}
    >
      {children}
    </motion.button>
  )
}
