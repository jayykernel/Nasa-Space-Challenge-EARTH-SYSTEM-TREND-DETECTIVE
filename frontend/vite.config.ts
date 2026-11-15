import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  // Cesium loads workers, textures, and widgets as static assets at runtime.
  // Serve the package's prebuilt asset directory from the site root in dev and builds.
  publicDir: path.resolve(__dirname, 'node_modules/cesium/Build/Cesium'),
  define: {
    CESIUM_BASE_URL: JSON.stringify('/'),
  },
  css: {
    postcss: {
      plugins: [tailwindcss(), autoprefixer()],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    // Keep Vite's bundle separate from Cesium's case-sensitive `Assets` directory.
    // On case-insensitive developer filesystems, `assets` otherwise merges with it
    // and the deployed HTML points at paths that are not present on Linux hosts.
    assetsDir: 'app-assets',
    sourcemap: false,
  },
})
