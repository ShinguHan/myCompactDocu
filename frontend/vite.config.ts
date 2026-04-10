import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function getPackageChunkName(id: string) {
  const normalizedId = id.split('\\').join('/')
  const parts = normalizedId.split('/node_modules/')[1]?.split('/') ?? []
  if (parts.length === 0) return undefined
  if (parts[0] === 'string-convert' || parts[0] === 'json2mq') return undefined
  if (parts[0].startsWith('@')) return `${parts[0].slice(1)}-${parts[1]}`
  return parts[0]
}

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 550,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          const normalizedId = id.split('\\').join('/')
          if (normalizedId.includes('/react-dom/') || normalizedId.includes('/react/')) return 'react-vendor'
          if (normalizedId.includes('/react-router') || normalizedId.includes('/@remix-run/')) return 'router'
          if (normalizedId.includes('/@tanstack/react-query/')) return 'query'
          if (normalizedId.includes('/axios/')) return 'axios'
          if (normalizedId.includes('/dayjs/')) return 'dayjs'
          if (normalizedId.includes('/recharts/')) return 'charts'
          return getPackageChunkName(id)
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
