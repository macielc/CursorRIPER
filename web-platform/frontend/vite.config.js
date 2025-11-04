import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname),  // FIX: Garante root correto
  server: {
    port: 3000,
    host: true,  // Permite acesso externo
    strictPort: false,  // Permite usar porta alternativa se 3000 ocupado
    fs: {
      strict: false,  // Permite acesso a arquivos fora do root
      allow: ['.']
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})

