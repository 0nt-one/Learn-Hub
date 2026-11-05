<script setup lang="ts">
import DashboardLayout from './DashboardLayout.vue'

const navigation = ['资源审核', '资源管理', '用户管理', '分类管理', '操作日志'] as const
</script>

<template>
  <DashboardLayout role="Admin" title="首页概览" breadcrumb-label="管理后台概览" :navigation="navigation">
    <slot />
  </DashboardLayout>
</template>
