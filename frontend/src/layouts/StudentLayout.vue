<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppBrand from '../components/common/AppBrand.vue'
import UserMenu from '../components/common/UserMenu.vue'
import NotificationCenter from '../components/common/NotificationCenter.vue'
import ResourceFormModal from '../components/resources/ResourceFormModal.vue'
import { useSession } from '../api/session'

/*
 * 学生端布局壳：无侧栏，内容最大宽 1440 居中。
 * 右上角是账号入口：已登录显示头像菜单，未登录显示登录按钮（首页可公开访问）。
 */
const route = useRoute()
const { isLoggedIn, currentUser, accessToken } = useSession()
const emit = defineEmits<{ resourceShared: [] }>()
const toast = useToast()
const shareOpen = ref(false)
const canShare = computed(() => isLoggedIn.value &&
  (currentUser.value?.role === 'student' || currentUser.value?.role === 'teacher'))

watch(accessToken, () => { shareOpen.value = false })

function onResourceShared() {
  if (!canShare.value) return
  toast.add({ title: '已保存为草稿', color: 'success' })
  emit('resourceShared')
}

const navigation = [
  { label: '发现', to: '/' },
  { label: '资源中心', to: '/resources' },
  { label: '学习进度', to: '/learning' },
] as const
</script>

<template>
  <div class="student-layout">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <header class="student-header">
      <div class="student-header__inner">
        <AppBrand />
        <nav aria-label="学生导航">
          <RouterLink
            v-for="item in navigation"
            :key="item.to"
            :to="item.to"
            :aria-current="route.path === item.to ? 'page' : undefined"
          >
            {{ item.label }}
          </RouterLink>
          <button v-if="canShare" type="button" aria-haspopup="dialog" @click="shareOpen = true">分享资源</button>
        </nav>
        <div class="student-header__actions">
          <NotificationCenter v-if="isLoggedIn" />
          <UserMenu v-if="isLoggedIn" />
          <UButton v-else :to="route.path === '/resources' ? { path: '/login', query: { redirect: route.fullPath } } : '/login'" color="primary" size="sm">登录</UButton>
        </div>
      </div>
    </header>
    <main id="main-content" class="student-main">
      <slot />
    </main>
    <footer class="student-footer">Learn-Hub · 学习资源共享平台</footer>
    <ResourceFormModal v-if="canShare" v-model:open="shareOpen" @saved="onResourceShared" />
  </div>
</template>

<style scoped>
.student-header {
  position: sticky;
  top: 0;
  z-index: 20;
  height: var(--lh-header-height);
  border-bottom: 1px solid var(--lh-border);
  background: var(--lh-surface);
}

.student-header__inner {
  display: flex;
  align-items: center;
  gap: 40px;
  width: 100%;
  max-width: var(--lh-student-max);
  height: 100%;
  margin: 0 auto;
  padding: 0 32px;
}

nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

nav :is(a, button) {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  color: var(--lh-text-secondary);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
}

nav :is(a, button):hover {
  background: var(--lh-surface-subtle);
  color: var(--lh-text);
}

nav button { cursor: pointer; }

nav a[aria-current='page'] {
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
  font-weight: 600;
}

.student-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.student-main {
  width: 100%;
  max-width: var(--lh-student-max);
  margin: 0 auto;
  padding: 24px 32px 64px;
}

.student-footer {
  padding: 0 24px 28px;
  color: var(--lh-text-secondary);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 767px) {
  .student-header {
    height: 56px;
  }

  .student-header__inner {
    gap: 8px;
    padding: 0 16px;
  }

  nav { min-width: 0; overflow-x: auto; }
  nav :is(a, button) {
    padding: 7px 10px;
  }

  .student-main {
    padding: 16px 16px 40px;
  }
}

@media (max-width: 479px) {
  .student-header__inner :deep(.brand__word) { display: none; }
  .student-header__inner { padding-inline: 8px; }
  .student-header__actions { gap: 4px; }
  nav :is(a, button) { padding-inline: 5px; }
}
</style>
