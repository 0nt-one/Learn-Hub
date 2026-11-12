<script setup lang="ts">
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'

/*
 * 异步区域容器：用单一判别字段表达五种状态，避免出现 loading + empty 这类矛盾组合。
 * 页面只负责把请求状态翻译成 status，视觉与文案在这里统一（docs/ui-design-spec.md 5.1）。
 */
const props = withDefaults(
  defineProps<{
    status: 'loading' | 'ready' | 'empty' | 'error' | 'unavailable'
    emptyTitle?: string
    emptyDescription?: string
    emptyIcon?: string
    unavailableTitle?: string
    unavailableDescription?: string
    unavailableIcon?: string
    errorTitle?: string
    errorDescription?: string
    /** 后端返回的 request_id，失败时显示，便于报障 */
    requestId?: string
    /** 加载骨架的行数，默认与常见列表行高一致 */
    skeletonRows?: number
  }>(),
  {
    emptyTitle: '暂无内容',
    emptyDescription: '当前条件下没有可显示的内容。',
    emptyIcon: 'i-lucide-inbox',
    unavailableTitle: '数据暂未接入',
    unavailableDescription: '接口接入后这里会显示真实数据。',
    unavailableIcon: 'i-lucide-plug',
    errorTitle: '加载失败',
    errorDescription: '请检查网络连接后重试。',
    requestId: '',
    skeletonRows: 3,
  },
)

const emit = defineEmits<{ retry: [] }>()

const isBusy = computed(() => props.status === 'loading')
</script>

<template>
  <div class="async-region" :aria-busy="isBusy ? 'true' : undefined">
    <template v-if="status === 'loading'">
      <span class="sr-only" role="status">正在加载</span>
      <slot name="skeleton">
        <div class="async-region__skeleton">
          <USkeleton v-for="row in skeletonRows" :key="row" class="async-region__bar" />
        </div>
      </slot>
    </template>

    <ErrorState
      v-else-if="status === 'error'"
      :title="errorTitle"
      :description="errorDescription"
      :request-id="requestId"
      @retry="emit('retry')"
    />

    <EmptyState
      v-else-if="status === 'empty'"
      :title="emptyTitle"
      :description="emptyDescription"
      :icon="emptyIcon"
    />
    
    <EmptyState
      v-else-if="status === 'unavailable'"
      :title="unavailableTitle"
      :description="unavailableDescription"
      :icon="unavailableIcon"
    />

    <slot v-else />
  </div>
</template>

<style scoped>
.async-region__skeleton {
  display: grid;
  gap: 12px;
  min-height: 104px;
  align-content: center;
}

.async-region__bar {
  height: 16px;
  border-radius: var(--radius-sm);
}

.async-region__bar:last-child {
  width: 60%;
}
</style>
