import './assets/main.css'
import { createApp } from 'vue'
import ui from '@nuxt/ui/vue-plugin'
import App from './App.vue'
import { router } from './router'
import { clearSession } from './api/session'
import { setUnauthorizedHandler } from './api/client'

/*
 * 会话失效统一处理：清空内存会话，带上当前路径回登录页。
 * 放在这里而不是各个页面里，是因为令牌会在"停留在页面上"时过期，
 * 那时路由守卫不会触发——只有请求失败能发现。
 */
setUnauthorizedHandler(() => {
  const redirect = router.currentRoute.value.fullPath
  clearSession()
  void router.replace({ name: 'login', query: { redirect } })
})

createApp(App).use(router).use(ui).mount('#app')
