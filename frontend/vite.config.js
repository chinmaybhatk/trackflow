import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      // Alias to CRM components if CRM is installed
      '@crm': path.resolve(__dirname, '../../../crm/frontend/src')
    }
  },
  build: {
    outDir: '../trackflow/public/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        'crm-sidebar': path.resolve(__dirname, 'src/components/Layouts/Sidebar.vue')
      },
      output: {
        format: 'es',
        entryFileNames: '[name].js'
      }
    }
  },
  server: {
    port: 8081
  }
})
