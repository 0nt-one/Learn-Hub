<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import AppBrand from '../components/common/AppBrand.vue'
import Breadcrumbs from '../components/common/Breadcrumbs.vue'

defineProps<{
  role: 'Teacher' | 'Admin'
  title: string
  breadcrumbLabel: string
  navigation: readonly string[]
}>()

const menuOpen = ref(false)
const collapsed = ref(false)
const menuButton = ref<HTMLButtonElement | null>(null)
const closeButton = ref<HTMLButtonElement | null>(null)
let previousOverflow = ''

function closeMenu(): void {
  menuOpen.value = false
  menuButton.value?.focus()
}

watch(menuOpen, (open) => {
  if (open) {
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    void nextTick(() => closeButton.value?.focus())
  } else {
    document.body.style.overflow = previousOverflow
  }
})

onUnmounted(() => {
  document.body.style.overflow = previousOverflow
})
</script>

<template>
  <div class="dashboard-layout" :class="{ 'dashboard-layout--collapsed': collapsed }">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <div v-if="menuOpen" class="dashboard-scrim" @click="closeMenu"></div>
    <aside class="dashboard-sidebar" :class="{ 'dashboard-sidebar--open': menuOpen }" aria-label="侧边导航"
      @keydown.esc="closeMenu">
      <div class="dashboard-sidebar__brand">
        <AppBrand />
        <span v-if="!collapsed" class="role-label">{{ role }}</span>
        <button ref="closeButton" class="sidebar-close" type="button" aria-label="关闭导航" @click="closeMenu">×</button>
      </div>
      <nav class="dashboard-nav" aria-label="工作台导航">
        <span class="dashboard-nav__active" aria-current="page" :title="collapsed ? title : undefined"><b
            aria-hidden="true">{{ title.slice(0, 1) }}</b><span>{{ title }}</span></span>
        <span v-for="item in navigation" :key="item" class="dashboard-nav__planned"
          :title="collapsed ? item : undefined"><b aria-hidden="true">{{ item.slice(0, 1) }}</b><span>{{ item
          }}</span><small>规划中</small></span>
      </nav>
      <div class="dashboard-sidebar__footer">Learn-Hub · 布局预览</div>
    </aside>
    <div class="dashboard-body">
      <header class="dashboard-toolbar">
        <button ref="menuButton" class="menu-button" type="button" :aria-label="menuOpen ? '关闭导航' : '打开导航'"
          :aria-expanded="menuOpen" @click="menuOpen = !menuOpen">☰</button>
        <button class="collapse-button" type="button" :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
          @click="collapsed = !collapsed">☰</button>
        <span>{{ role }} 工作台</span>
        <span class="dashboard-toolbar__note">页面模板预览</span>
      </header>
      <main id="main-content" class="dashboard-main">
        <Breadcrumbs :items="[{ label: '首页', to: '/' }, { label: breadcrumbLabel }]" />
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  --sidebar-width: 240px;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
}

.dashboard-layout--collapsed {
  --sidebar-width: 72px;
}

.dashboard-sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: auto;
  border-right: 1px solid var(--lh-border);
  background: white;
}

.dashboard-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 64px;
  padding: 0 20px;
  border-bottom: 1px solid var(--lh-border);
}

.dashboard-layout--collapsed .dashboard-sidebar__brand {
  padding-left: 21px;
}

.dashboard-layout--collapsed .dashboard-sidebar__brand :deep(.brand > span:last-child) {
  display: none;
}

.role-label {
  color: var(--lh-primary);
  font-size: 13px;
}

.dashboard-nav {
  display: grid;
  gap: 6px;
  padding: 20px 12px;
}

.dashboard-nav>span {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  white-space: nowrap;
}

.dashboard-nav b {
  display: none;
  font-size: 14px;
}

.dashboard-nav__active {
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
  font-weight: 700;
  border-left: 3px solid var(--lh-primary);
}

.dashboard-nav__planned {
  color: var(--lh-text-secondary);
}

.dashboard-nav small {
  color: #75839a;
  font-size: 11px;
}

.dashboard-layout--collapsed .dashboard-nav>span {
  justify-content: center;
  padding: 10px;
}

.dashboard-layout--collapsed .dashboard-nav b {
  display: block;
}

.dashboard-layout--collapsed .dashboard-nav span span,
.dashboard-layout--collapsed .dashboard-nav small {
  display: none;
}

.dashboard-sidebar__footer {
  margin-top: auto;
  padding: 20px;
  color: var(--lh-text-secondary);
  font-size: 11px;
}

.dashboard-layout--collapsed .dashboard-sidebar__footer {
  display: none;
}

.dashboard-toolbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--lh-border);
  background: white;
  font-weight: 600;
}

.dashboard-toolbar__note {
  margin-left: auto;
  color: var(--lh-text-secondary);
  font-size: 12px;
  font-weight: 400;
}

.dashboard-main {
  width: min(100%, 1760px);
  margin: auto;
  padding: 24px;
}

.menu-button,
.collapse-button,
.sidebar-close {
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--lh-text);
  font-size: 19px;
}

.menu-button:hover,
.collapse-button:hover,
.sidebar-close:hover {
  background: var(--lh-primary-soft);
}

.menu-button,
.sidebar-close,
.dashboard-scrim {
  display: none;
}

@media (max-width: 1023px) {
  .dashboard-layout {
    display: block;
  }

  .dashboard-sidebar {
    position: fixed;
    z-index: 50;
    width: min(320px, 88vw);
    visibility: hidden;
    transform: translateX(-100%);
    transition: transform 180ms ease, visibility 180ms ease;
  }

  .dashboard-sidebar--open {
    visibility: visible;
    transform: translateX(0);
  }

  .dashboard-scrim {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgb(11 21 53 / 40%);
  }

  .menu-button,
  .sidebar-close {
    display: block;
  }

  .sidebar-close {
    margin-left: auto;
  }

  .collapse-button {
    display: none;
  }
}

@media (max-width: 767px) {
  .dashboard-toolbar {
    height: 56px;
    padding: 0 16px;
  }

  .dashboard-main {
    padding: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-sidebar {
    transition: none;
  }
}
</style>
