import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import ui from '@nuxt/ui/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')

  return {
    plugins: [
      vue(),
      ui({
        // 首版只有浅色设计，关闭系统暗色自动切换，避免页面在深色系统下变黑。
        colorMode: false,
        // 扫描模板中用到的 i-lucide-* 图标并打包进产物，避免运行时请求 iconify CDN。
        icon: { clientBundle: { scan: true } },
      }),
    ],
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      proxy: {
        '/health': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: '127.0.0.1',
      port: 4173,
      strictPort: true,
    },
  }
})
