import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// Vazirmatn — local fontsource (offline-first, NFR-1)
import '@fontsource/vazirmatn/400.css'
import '@fontsource/vazirmatn/500.css'
import '@fontsource/vazirmatn/700.css'

import App from './app/App'
import './styles/globals.css'

// RTL + fa (doc 07.2)
document.documentElement.dir = 'rtl'
document.documentElement.lang = 'fa'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
