import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),
            //  tailwindcss(),
  ],
  root: './', // root directory of your project
  build: {
    outDir: 'dist',  // This is where the production build will go
    emptyOutDir: true
  }
})
