/** Card — soft card with gentle shadow (doc 07.2). */
import type { HTMLAttributes } from 'react'

export function Card({ className = '', ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={['rounded-lg border border-border bg-surface shadow-soft', className].join(' ')}
      {...rest}
    />
  )
}
