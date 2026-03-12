import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/room-app/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/room': 'http://localhost:8000',
      '/cognitive': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
