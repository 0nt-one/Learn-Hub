<script setup lang="ts">
import DashboardLayout from './DashboardLayout.vue'

const navigation = ['我的资源', '共享新资源', '审核结果', '课程审核'] as const
</script>

<template>
  <DashboardLayout role="Teacher" title="工作台" breadcrumb-label="教师工作台" :navigation="navigation">
    <slot />
  </DashboardLayout>
</template>
