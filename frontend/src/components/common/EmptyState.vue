<script setup lang="ts">
defineProps<{ title: string; description: string; symbol?: string }>()
</script>

<template>
  <div class="empty-state">
    <span class="empty-state__symbol" aria-hidden="true">{{ symbol || '◇' }}</span>
    <div>
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 104px;
}

.empty-state__symbol {
  display: grid;
  flex: none;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: 12px;
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
  font-size: 28px;
}

h3 {
  margin: 0 0 4px;
  font-size: 15px;
  line-height: 24px;
}

p {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 13px;
  line-height: 20px;
}
</style>
