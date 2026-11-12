<script setup lang="ts">
import { computed } from 'vue'
import type { ResourceType } from '../../types/resource'

/*
 * 资源类型徽章：首版只有 document / video / link 三种，
 * 不按文件格式（PDF、ZIP 等）细分（docs/ui-design-spec.md 1.3）。
 */
const TYPE_META = {
  document: { label: '文档', icon: 'i-lucide-file-text', color: 'primary' },
  video: { label: '视频', icon: 'i-lucide-video', color: 'secondary' },
  link: { label: '链接', icon: 'i-lucide-link-2', color: 'success' },
} as const

const props = defineProps<{ type: ResourceType }>()

const meta = computed(() => TYPE_META[props.type])
</script>

<template>
  <UBadge :color="meta.color" variant="soft" size="sm" :icon="meta.icon">
    {{ meta.label }}
  </UBadge>
</template>
