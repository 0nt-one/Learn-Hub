<script setup lang="ts">
defineProps<{
  label: string
  value?: string | number
  state?: 'ready' | 'loading' | 'unavailable'
}>()
</script>

<template>
  <div class="stat-card" :aria-busy="state === 'loading'">
    <p class="stat-card__label">{{ label }}</p>
    <p v-if="state === 'loading'" class="stat-card__value">加载中</p>
    <p v-else-if="state === 'ready' && value !== undefined" class="stat-card__value">{{ value }}</p>
    <p v-else class="stat-card__value">—</p>
    <p v-if="state !== 'ready'" class="stat-card__hint">
      {{ state === 'loading' ? '正在获取数据' : '数据暂未接入' }}
    </p>
  </div>
</template>

<style scoped>
.stat-card {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--lh-border);
  border-radius: 12px;
  background: var(--lh-surface);
}

.stat-card__label {
  margin: 0 0 12px;
  color: var(--lh-text-secondary);
  font-size: 14px;
}

.stat-card__value {
  margin: 0;
  font-size: 32px;
  line-height: 40px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.stat-card__hint {
  margin: 8px 0 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

@media (max-width: 767px) {
  .stat-card {
    padding: 16px;
  }

  .stat-card__value {
    font-size: 28px;
  }
}
</style>
