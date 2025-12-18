import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react' // Ensure you have the react plugin imported

export default defineConfig({
  base: './', // CRITICAL: This makes all paths relative
  plugins: [
    react(),
    tailwindcss(),
  ],
})