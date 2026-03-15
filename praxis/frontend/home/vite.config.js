import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/home-assets/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5174,
    proxy: {
      '/search': 'http://localhost:8000',
      '/feedback': 'http://localhost:8000',
      '/categories': 'http://localhost:8000',
    },
  },
});
