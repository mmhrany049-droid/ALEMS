import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// doc 03 §3.2 — frontend 5173, proxy -> backend 127.0.0.1:8010
// doc 02 NFR-4 / PROJECT_MANIFEST: default ports
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // 0.0.0.0 so the sandbox/preview can reach it
    port: 5173,
    strictPort: true,
    // Allow the sandbox preview host header (avoids Vite's host-block).
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
      // /health is served at the root of the backend, not under /api
      '/health': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8010', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8010', changeOrigin: true },
    },
  },
})
