<script setup lang="ts">
/*
 * 局部失败状态：说明发生了什么 + 手动重试 + 可选的 request_id。
 * 只展示安全信息，不呈现 SQL、堆栈或令牌（docs/ui-design-spec.md 5.1 / 12.3）。
 */
withDefaults(
  defineProps<{
    title?: string
    description?: string
    /** 后端返回的 request_id，便于用户报障时对照日志 */
    requestId?: string
    retryLabel?: string
  }>(),
  {
    title: '加载失败',
    description: '请检查网络连接后重试。',
    requestId: '',
    retryLabel: '重试',
  },
)

const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="error-state" role="alert">
    <div class="error-state__body">
      <span class="error-state__icon-wrap" aria-hidden="true">
        <UIcon name="i-lucide-triangle-exclamation-point" class="error-state__icon" />
      </span>
      <div class="error-state__text">
        <h3 class="error-state__title">{{ title }}</h3>
        <p class="error-state__description">{{ description }}</p>
        <p v-if="requestId" class="error-state__request-id">请求编号 {{ requestId }}</p>
      </div>
    </div>
    <UButton
      color="neutral"
      variant="outline"
      size="sm"
      icon="i-lucide-refresh-cw"
      @click="emit('retry')"
    >
      {{ retryLabel }}
    </UButton>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 104px;
  padding: 16px;
  border: 1px solid var(--lh-danger);
  border-radius: var(--radius-lg);
  background: var(--lh-danger-soft);
}

.error-state__body {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.error-state__icon-wrap {
  display: grid;
  flex: none;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--lh-surface);
  color: var(--lh-danger);
}

.error-state__icon {
  width: 20px;
  height: 20px;
}

.error-state__text {
  min-width: 0;
}

.error-state__title {
  margin: 0 0 4px;
  color: var(--lh-danger);
  font-size: 15px;
  font-weight: 600;
  line-height: 24px;
}

.error-state__description {
  margin: 0;
  color: var(--lh-text);
  font-size: 13px;
  line-height: 20px;
}

.error-state__request-id {
  margin: 6px 0 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 767px) {
  .error-state {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
