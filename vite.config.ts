import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        try: 'try.html',
      },
    },
  },
  server: {
    proxy: {
      // local Python stand-in for the Vercel functions: python scripts/dev_api.py
      '/api': 'http://localhost:5050',
    },
  },
})
