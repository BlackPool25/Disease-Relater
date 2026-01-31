/**
 * Vite Configuration for Disease Visualizer Frontend
 * 
 * Configures React + Tailwind CSS with optimized build settings
 * for the disease network visualization application.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  
  // Development server configuration
  server: {
    port: 3000,
    // Proxy API requests to backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  },
  
  // Build optimization
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          'three': ['three'],
          'react-three': ['@react-three/fiber', '@react-three/drei'],
        }
      }
    }
  }
})
