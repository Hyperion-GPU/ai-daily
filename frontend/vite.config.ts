import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }

          if (
            id.includes('/css-render/') ||
            id.includes('\\css-render\\') ||
            id.includes('/@css-render/') ||
            id.includes('\\@css-render\\') ||
            id.includes('/seemly/') ||
            id.includes('\\seemly\\') ||
            id.includes('/vooks/') ||
            id.includes('\\vooks\\') ||
            id.includes('/vdirs/') ||
            id.includes('\\vdirs\\') ||
            id.includes('/evtd/') ||
            id.includes('\\evtd\\')
          ) {
            return 'naive-runtime'
          }

          if (
            id.includes('/naive-ui/') ||
            id.includes('\\naive-ui\\') ||
            id.includes('/vueuc/') ||
            id.includes('\\vueuc\\') ||
            id.includes('/treemate/') ||
            id.includes('\\treemate\\')
          ) {
            return 'naive-ui'
          }

          if (id.includes('/@vicons/') || id.includes('\\@vicons\\')) {
            return 'icons'
          }

          if (
            id.includes('/axios/') ||
            id.includes('\\axios\\') ||
            id.includes('/dayjs/') ||
            id.includes('\\dayjs\\')
          ) {
            return 'utils'
          }
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
