import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = process.env.BACKEND_URL || env.VITE_BACKEND_URL || (process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://backend:8000');
  const wsTarget = target.replace(/^http/, 'ws');

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 3000,
      proxy: {
        '/api': {
          target: process.env.BACKEND_URL || env.VITE_BACKEND_URL || 'http://backend:8000',
          changeOrigin: true
        },
        '/ws': {
          target: (process.env.BACKEND_URL || env.VITE_BACKEND_URL || 'http://backend:8000').replace(/^http/, 'ws'),
          ws: true
        }
      }
    }
  }
})
