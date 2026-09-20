/** Spinner — non-animated under prefers-reduced-motion (CSS handles it). */
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <span
      className="inline-block animate-spin rounded-full border-2 border-border border-t-primary"
      style={{ width: size, height: size }}
      role="status"
      aria-label="در حال بارگذاری"
    />
  )
}
