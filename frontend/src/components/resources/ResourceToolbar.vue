<script setup lang="ts">
import type { ResourceSort } from '../../types/resource'

/*
 * 资源工具条：真实总数、排序。总数来自服务端 total，不用当前页条数代替。
 * 总数接口未接入时显示“—”后面的说明，而不是写死 0。
 */
const props = defineProps<{
  total: number | null
  sort: ResourceSort
  loading?: boolean
  view?: 'grid' | 'list'
}>()

const emit = defineEmits<{ 'update:sort': [value: ResourceSort]; 'update:view': [value: 'grid' | 'list'] }>()

const SORT_OPTIONS: { value: ResourceSort; label: string }[] = [
  { value: 'newest', label: '最新' },
  { value: 'title', label: '标题' },
]

function onSortChange(value: unknown): void {
  emit('update:sort', value === 'title' ? 'title' : 'newest')
}
</script>

<template>
  <div class="resource-toolbar">
    <p class="resource-toolbar__total" role="status" aria-live="polite">
      <span v-if="loading">正在查找</span>
      <span v-else-if="total === null">资源总数待获取</span>
      <span v-else>共 {{ total }} 条</span>
    </p>

    <div class="resource-toolbar__actions">
      <label class="resource-toolbar__label" for="resource-sort">排序</label>
      <USelect
        id="resource-sort"
        :model-value="props.sort"
        :items="SORT_OPTIONS"
        size="sm"
        class="resource-toolbar__select"
        @update:model-value="onSortChange"
      />
      <UButton icon="i-lucide-layout-grid" :variant="view === 'grid' ? 'soft' : 'ghost'" color="primary"
        aria-label="卡片视图" :aria-pressed="view === 'grid'" @click="emit('update:view', 'grid')" />
      <UButton icon="i-lucide-list" :variant="view === 'list' ? 'soft' : 'ghost'" color="primary"
        aria-label="列表视图" :aria-pressed="view === 'list'" @click="emit('update:view', 'list')" />
    </div>
  </div>
</template>

<style scoped>
.resource-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  border: 1px solid var(--lh-border);
  border-radius: var(--radius-lg);
  background: var(--lh-surface);
}

.resource-toolbar__total {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.resource-toolbar__actions {
  display: flex;
  flex: none;
  align-items: center;
  gap: 8px;
}

.resource-toolbar__label {
  color: var(--lh-text-secondary);
  font-size: 13px;
}

.resource-toolbar__select {
  width: 108px;
}

@media (max-width: 767px) {
  .resource-toolbar {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
