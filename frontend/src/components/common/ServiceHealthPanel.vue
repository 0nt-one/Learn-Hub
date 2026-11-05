<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { checkBackendHealth } from '../../api/health'

const status = ref<'checking' | 'ok' | 'error'>('checking')

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
  <section class="health-panel" aria-labelledby="health-title">
    <div>
      <h2 id="health-title">后端连接状态</h2>
      <p>健康检查使用真实接口。</p>
    </div>
    <div class="health-panel__action">
      <span :class="['health-panel__dot', status]" aria-hidden="true"></span>
      <span role="status" aria-live="polite">{{ status === 'checking' ? '检查中' : status === 'ok' ? '服务正常' : '连接失败'
        }}</span>
      <UButton color="primary" variant="outline" :loading="status === 'checking'" @click="refresh">重试</UButton>
    </div>
  </section>
</template>

<style scoped>
.health-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 24px;
  border: 1px solid var(--lh-border);
  border-radius: 12px;
  background: white;
}

h2 {
  margin: 0 0 3px;
  font-size: 15px;
}

p {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.health-panel__action {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  white-space: nowrap;
}

.health-panel__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a6b0c0;
}

.health-panel__dot.ok {
  background: var(--lh-success);
}

.health-panel__dot.error {
  background: var(--lh-danger);
}

@media (max-width: 767px) {
  .health-panel {
    align-items: start;
    flex-direction: column;
    padding: 16px;
  }
}
</style>
