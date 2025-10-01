import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/app/',
  server: {
    hmr: {
      clientPort: 5173, // Use direct port for HMR, bypassing proxy
    },
  },
})
