/** Minimal inline icon set (offline-first, no external icon CDN). */
import type { SVGProps } from 'react'

type P = SVGProps<SVGSVGElement> & { name: IconName; size?: number }

export type IconName =
  | 'home'
  | 'book'
  | 'test'
  | 'review'
  | 'plan'
  | 'exam'
  | 'progress'
  | 'settings'
  | 'sun'
  | 'moon'
  | 'check'
  | 'book-open'
  | 'sparkle'
  | 'clock'
  | 'target'
  | 'more'
  | 'alert'
  | 'focus'
  | 'download'
  | 'shield'
  | 'x'

const PATHS: Record<IconName, React.ReactNode> = {
  home: <path d="M3 10.5 12 3l9 7.5M5 9.5V21h14V9.5" />,
  book: <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17.5H6.5A2.5 2.5 0 0 0 4 22zM4 19.5A2.5 2.5 0 0 1 6.5 17H20" />,
  test: <path d="M9 3h6v3.5H9zM7 6.5h10v14H7zM10 11h4M10 15h4" />,
  review: <path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5" />,
  plan: <path d="M5 5h14v16H5zM5 9h14M9 3v4M15 3v4" />,
  exam: <path d="M4 4h16v16H4zM8 8h8M8 12h8M8 16h5" />,
  progress: <path d="M4 20V10M10 20V4M16 20v-8M21 20H3" />,
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 9 19.35a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.55-1.03H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.65 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.65a1.7 1.7 0 0 0 1.03-1.56V3a2 2 0 1 1 4 0v.09c0 .68.4 1.3 1.03 1.56a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87c.26.62.88 1.03 1.56 1.03H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.56 1.03z" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />,
  check: <path d="M4 12.5 9.5 18 20 6.5" />,
  'book-open': <path d="M12 6c-1.5-1.2-3.5-2-6-2H3v14h3c2.5 0 4.5.8 6 2 1.5-1.2 3.5-2 6-2h3V4h-3c-2.5 0-4.5.8-6 2zM12 6v14" />,
  sparkle: <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9zM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.2" />
    </>
  ),
  more: <path d="M12 12h.01M12 5h.01M12 19h.01" />,
  alert: <path d="M12 3 2.5 20h19zM12 9.5v5M12 17.5h.01" />,
  focus: (
    <>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </>
  ),
  download: <path d="M12 3v12M7 10.5l5 5 5-5M4 21h16" />,
  shield: <path d="M12 3l8 3v6c0 4.5-3.5 7.5-8 9-4.5-1.5-8-4.5-8-9V6z" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
}

export function Icon({ name, size = 20, ...rest }: P) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  )
}
