<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DashboardLayout from './DashboardLayout.vue'

const route = useRoute()

/** 顶栏标题来自路由 meta，未标注时回落到工作台 */
const title = computed(() => String(route.meta.title ?? '教师工作台'))

const navigation = [
  { label: '工作台', icon: 'i-lucide-layout-dashboard', to: '/teacher' },
  { label: '我的课程', icon: 'i-lucide-book-open', to: '/teacher/courses' },
  { label: '我的资源', icon: 'i-lucide-folder', to: '/teacher/resources' },
  // 「共享新资源」不放入口，统一从「我的资源」页右上角按钮进入
  { label: '课程审核', icon: 'i-lucide-shield-check', to: '/teacher/reviews' },
  // 离开工作台，回到面向学生的主站；和上面的业务菜单用分隔线隔开
  { label: '返回前台', icon: 'i-lucide-house', to: '/', dividerBefore: true },
] as const
</script>

<template>
  <DashboardLayout role="Teacher" :title="title" :navigation="navigation">
    <slot />
  </DashboardLayout>
</template>
