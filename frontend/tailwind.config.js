/** @type {import('tailwindcss').Config} */
// doc 07.3 — tokens live in src/styles/tokens.css; Tailwind maps to them.
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--color-bg)',
        surface: 'var(--color-surface)',
        'surface-2': 'var(--color-surface-2)',
        border: 'var(--color-border)',
        primary: 'var(--color-primary)',
        'primary-soft': 'var(--color-primary-soft)',
        success: 'var(--color-success)',
        'success-soft': 'var(--color-success-soft)',
        danger: 'var(--color-danger)',
        'danger-soft': 'var(--color-danger-soft)',
        warning: 'var(--color-warning)',
        'warning-soft': 'var(--color-warning-soft)',
        review: 'var(--color-review)',
        'review-soft': 'var(--color-review-soft)',
        ink: 'var(--color-text)',
        muted: 'var(--color-text-muted)',
      },
      borderRadius: {
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      spacing: {
        1: 'var(--space-1)',
        2: 'var(--space-2)',
        3: 'var(--space-3)',
        4: 'var(--space-4)',
        5: 'var(--space-5)',
        6: 'var(--space-6)',
      },
      fontSize: {
        'body-sm': 'var(--font-body-sm)',
        body: 'var(--font-body)',
        'body-lg': 'var(--font-body-lg)',
        'title-sm': 'var(--font-title-sm)',
        title: 'var(--font-title)',
        'title-lg': 'var(--font-title-lg)',
        display: 'var(--font-display)',
        'display-lg': 'var(--font-display-lg)',
      },
      fontFamily: {
        sans: ['Vazirmatn', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
      },
      transitionDuration: {
        fast: 'var(--motion-fast)',
        normal: 'var(--motion-normal)',
        slow: 'var(--motion-slow)',
      },
    },
  },
  plugins: [],
}
