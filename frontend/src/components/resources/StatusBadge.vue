<script setup lang="ts">
import { computed } from 'vue'
import type { ResourceStatus } from '../../types/resource'

/*
 * 资源状态徽章：显示名与视觉来自 docs/ui-design-spec.md 5.2，
 * 文字 + 图标同时表达，不只靠颜色。
 */
const STATUS_META = {
  draft: { label: '草稿', color: 'neutral', icon: 'i-lucide-pen-line' },
  pending: { label: '待审核', color: 'warning', icon: 'i-lucide-clock' },
  approved: { label: '已发布', color: 'success', icon: 'i-lucide-circle-check' },
  rejected: { label: '已驳回', color: 'error', icon: 'i-lucide-circle-x' },
  archived: { label: '已归档', color: 'neutral', icon: 'i-lucide-archive' },
} as const

const props = withDefaults(
  defineProps<{
    status: ResourceStatus
    /** 审核结果语境下 approved 读作“已通过” */
    context?: 'resource' | 'review'
  }>(),
  { context: 'resource' },
)

const meta = computed(() => STATUS_META[props.status])

const label = computed(() =>
  props.status === 'approved' && props.context === 'review' ? '已通过' : meta.value.label,
)
</script>

<template>
  <UBadge :color="meta.color" variant="soft" size="sm" :icon="meta.icon">
    {{ label }}
  </UBadge>
</template>
