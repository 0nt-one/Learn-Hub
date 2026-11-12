<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DashboardLayout from './DashboardLayout.vue'

const route = useRoute()

/** 顶栏标题来自路由 meta，未标注时回落到概览页 */
const title = computed(() => String(route.meta.title ?? '首页概览'))

const navigation = [
  { label: '首页概览', icon: 'i-lucide-layout-dashboard', to: '/admin' },
  { label: '资源审核', icon: 'i-lucide-clipboard-check', to: '/admin/reviews' },
  { label: '资源管理', icon: 'i-lucide-library', to: '/admin/resources' },
  { label: '课程管理', icon: 'i-lucide-book-open', to: '/admin/courses' },
  { label: '用户管理', icon: 'i-lucide-users', to: '/admin/users' },
  { label: '分类管理', icon: 'i-lucide-tags', to: '/admin/categories' },
  { label: '操作日志', icon: 'i-lucide-scroll-text', to: '/admin/operation-logs' },
  // 离开工作台，回到面向学生的主站；和上面的业务菜单用分隔线隔开
  { label: '返回前台', icon: 'i-lucide-house', to: '/', dividerBefore: true },
] as const
</script>

<template>
  <DashboardLayout role="Admin" :title="title" :navigation="navigation">
    <slot />
  </DashboardLayout>
</template>
