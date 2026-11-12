<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { checkBackendHealth } from '../../api/health'

/*
 * 真实健康检查：状态文字 + 图标，不用颜色单独承担语义。
 * 具体请求策略（超时、错误归一化）仍在 api/health.ts。
 */
const status = ref<'checking' | 'ok' | 'error'>('checking')

const badge = computed(() => {
  if (status.value === 'ok') {
    return { color: 'success' as const, icon: 'i-lucide-circle-check', label: '服务正常' }
  }
  if (status.value === 'error') {
    return { color: 'error' as const, icon: 'i-lucide-circle-x', label: '连接失败' }
  }
  return { color: 'neutral' as const, icon: 'i-lucide-loader-circle', label: '检查中' }
})

async function refresh(): Promise<void> {
  status.value = 'checking'
  try {
    status.value = (await checkBackendHealth()) ? 'ok' : 'error'
  } catch {
    status.value = 'error'
  }
}

onMounted(() => void refresh())
</script>

<template>
  <UCard as="section" aria-labelledby="health-title" :ui="{ body: 'p-4 sm:px-6 sm:py-4' }">
    <div class="health-panel">
      <div>
        <h2 id="health-title" class="health-panel__title">后端连接状态</h2>
        <p class="health-panel__note">健康检查使用真实接口。</p>
      </div>
      <div class="health-panel__action">
        <UBadge
          :color="badge.color"
          variant="soft"
          :icon="badge.icon"
          role="status"
          aria-live="polite"
        >
          {{ badge.label }}
        </UBadge>
        <UButton color="primary" variant="outline" size="sm" :loading="status === 'checking'" @click="refresh">
          重试
        </UButton>
      </div>
    </div>
  </UCard>
</template>

<style scoped>
.health-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.health-panel__title {
  margin: 0 0 3px;
  color: var(--lh-text);
  font-size: 15px;
  font-weight: 600;
}

.health-panel__note {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.health-panel__action {
  display: flex;
  align-items: center;
  gap: 12px;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .health-panel {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
  }
}
</style>
