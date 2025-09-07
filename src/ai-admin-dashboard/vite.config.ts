import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5024',
        changeOrigin: true,
      },
      '/chat/ws': {
        target: 'ws://localhost:5024',
        ws: true,
      }
    }
  }
})