import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        ws: true,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('[ws proxy] error:', err.message);
          });
          proxy.on('proxyReqWs', (_proxyReq, _req, socket) => {
            socket.on('error', (err) => {
              console.log('[ws socket] error:', err.message);
            });
          });
        },
      },
    },
  },
  build: {
    // Enable source maps for debugging production issues
    sourcemap: false,
    // Increase chunk size warning limit for large PDF library
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Core React runtime - changes rarely
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Animation library - moderate size
          'framer-motion': ['framer-motion'],
          // Markdown rendering - used only in report view
          'markdown': ['react-markdown', 'remark-gfm'],
          // PDF viewer - large, loaded on demand
          'pdf-viewer': ['react-pdf-highlighter-extended'],
        },
      },
    },
    // Minification options
    minify: 'esbuild',
    target: 'es2022',
  },
});
