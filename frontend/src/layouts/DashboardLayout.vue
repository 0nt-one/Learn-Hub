<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppBrand from '../components/common/AppBrand.vue'
import UserMenu from '../components/common/UserMenu.vue'
import NotificationCenter from '../components/common/NotificationCenter.vue'
import { useSession } from '../api/session'

/*
 * 教师 / 管理员共用的后台布局壳。
 * 侧栏、移动抽屉、折叠与关闭按钮都由 Nuxt UI 的 USidebar 提供，
 * 这里只负责角色导航配置、折叠偏好持久化和工具栏。
 * 后台采用“平铺”结构：页面标题放在顶栏里，内容区直接从数据开始。
 */
defineProps<{
  role: 'Teacher' | 'Admin'
  title: string
  navigation: readonly {
    label: string
    icon: string
    to?: string
    /** 在这一项之前画一条分隔线，用来把"离开工作台"类的入口和业务菜单分开 */
    dividerBefore?: boolean
  }[]
}>()

/** 与 USidebar 的 breakpoint="lg" 保持一致：64rem = 1024px。 */
const DESKTOP_QUERY = '(min-width: 64rem)'
const STORAGE_KEY = 'learn-hub:dashboard-sidebar-open'

const route = useRoute()
const { isLoggedIn } = useSession()
const mediaQuery = window.matchMedia(DESKTOP_QUERY)
const isDesktop = ref(mediaQuery.matches)
const sidebarOpen = ref(isDesktop.value ? readOpenPreference() : false)

function readOpenPreference(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) !== 'false'
  } catch {
    return true
  }
}

function writeOpenPreference(open: boolean): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(open))
  } catch {
    // 隐私模式等无法写入时忽略，不影响使用。
  }
}

function handleBreakpointChange(event: MediaQueryListEvent): void {
  isDesktop.value = event.matches
  sidebarOpen.value = event.matches ? readOpenPreference() : false
}

mediaQuery.addEventListener('change', handleBreakpointChange)
onUnmounted(() => mediaQuery.removeEventListener('change', handleBreakpointChange))

watch(sidebarOpen, (open) => {
  if (isDesktop.value) writeOpenPreference(open)
})

watch(
  () => route.fullPath,
  () => {
    if (!isDesktop.value) sidebarOpen.value = false
  },
)

const toggleLabel = computed(() => (sidebarOpen.value ? '收起导航' : '展开导航'))

/** 当前路由与菜单项精确匹配时才高亮；没有 to 的是「规划中」占位项 */
function isActive(item: { to?: string }): boolean {
  return item.to !== undefined && route.path === item.to
}
</script>

<template>
  <div class="dashboard-shell">
    <a class="skip-link" href="#main-content">跳到主要内容</a>

    <USidebar
      v-model:open="sidebarOpen"
      :style="{
        '--sidebar-width': 'var(--lh-sidebar-width)',
        '--sidebar-width-icon': 'var(--lh-sidebar-collapsed-width)',
      }"
      collapsible="icon"
      variant="sidebar"
      breakpoint="lg"
      :rail="false"
      title="主导航"
      :ui="{ inner: 'bg-default' }"
      :menu="{ ui: { content: 'w-[min(320px,88vw)] sm:max-w-none' } }"
    >
      <template #header="{ state }">
        <AppBrand :wordmark="state === 'expanded'" />
        <span v-if="state === 'expanded'" class="dashboard-sidebar__role">{{ role }}</span>
      </template>

      <template #default="{ state }">
        <nav
          class="dashboard-nav"
          :class="{ 'dashboard-nav--collapsed': state === 'collapsed' }"
          aria-label="工作台导航"
        >
          <template v-for="item in navigation" :key="item.label">
            <hr v-if="item.dividerBefore" class="dashboard-nav__divider" aria-hidden="true" />
            <component
              :is="item.to ? 'RouterLink' : 'span'"
              class="dashboard-nav__item"
              :class="{ 'dashboard-nav__item--active': isActive(item) }"
              :to="item.to"
              :aria-current="isActive(item) ? 'page' : undefined"
              :title="state === 'collapsed' ? item.label : undefined"
            >
              <UIcon :name="item.icon" class="dashboard-nav__icon" aria-hidden="true" />
              <span v-if="state === 'expanded'" class="dashboard-nav__label">{{ item.label }}</span>
              <UBadge
                v-if="state === 'expanded' && !item.to"
                color="neutral"
                variant="soft"
                size="sm"
              >
                规划中
              </UBadge>
            </component>
          </template>
        </nav>
      </template>

      <template #footer="{ state }">
        <p v-if="state === 'expanded'" class="dashboard-sidebar__note">Learn-Hub</p>
      </template>
    </USidebar>

    <div class="dashboard-body">
      <header class="dashboard-toolbar">
        <UButton
          color="neutral"
          variant="ghost"
          size="sm"
          :icon="sidebarOpen ? 'i-lucide-panel-left-close' : 'i-lucide-panel-left-open'"
          :aria-label="toggleLabel"
          :aria-expanded="sidebarOpen"
          @click="sidebarOpen = !sidebarOpen"
        />
        <h1 class="dashboard-toolbar__title">{{ title }}</h1>
        <div class="dashboard-toolbar__actions">
          <slot name="actions" />
          <NotificationCenter v-if="isLoggedIn" />
          <UserMenu v-if="isLoggedIn" />
          <UButton v-else to="/login" color="primary" size="sm">登录</UButton>
        </div>
      </header>

      <main id="main-content" class="dashboard-main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard-shell {
  display: flex;
  min-height: 100vh;
}

/* 展开/折叠宽度由上面的内联 --sidebar-width* 变量决定，对齐规范的 240 / 72。 */
.dashboard-sidebar__role {
  color: var(--lh-primary);
  font-size: 13px;
  font-weight: 600;
}

.dashboard-sidebar__note {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 11px;
}

.dashboard-nav {
  display: grid;
  gap: 6px;
}

.dashboard-nav__divider {
  margin: 6px 4px;
  border: 0;
  border-top: 1px solid var(--lh-border);
}

.dashboard-nav__item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  color: var(--lh-text-secondary);
  font-size: 14px;
  text-decoration: none;
}

a.dashboard-nav__item:hover {
  background: var(--lh-surface-subtle);
  color: var(--lh-text);
}

.dashboard-nav__item--active {
  background: var(--lh-primary-soft);
  box-shadow: inset 3px 0 0 var(--lh-primary);
  color: var(--lh-primary);
  font-weight: 600;
}

.dashboard-nav__icon {
  flex: none;
  width: 20px;
  height: 20px;
}

.dashboard-nav__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.dashboard-nav--collapsed .dashboard-nav__item {
  justify-content: center;
  padding-inline: 0;
}

.dashboard-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.dashboard-toolbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 12px;
  height: var(--lh-header-height);
  padding: 0 24px;
  border-bottom: 1px solid var(--lh-border);
  background: var(--lh-surface);
}

.dashboard-toolbar__title {
  margin: 0;
  color: var(--lh-text);
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
}

.dashboard-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.dashboard-main {
  width: 100%;
  max-width: var(--lh-content-max);
  margin: 0 auto;
  padding: 24px 24px 64px;
}

@media (max-width: 767px) {
  .dashboard-toolbar {
    height: 56px;
    padding: 0 16px;
  }

  .dashboard-main {
    padding: 16px 16px 40px;
  }
}
</style>
