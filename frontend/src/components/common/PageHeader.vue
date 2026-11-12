<script setup lang="ts">
/*
 * 页面标题区：每页唯一 H1，标题、说明和右侧动作放这里。
 * 组件本身不请求数据，也不嵌套第二个 H1（docs/ui-design-spec.md 3.2 / 10.1）。
 */
withDefaults(
  defineProps<{
    title: string
    eyebrow: string
    description?: string
  }>(),
  { description: '' },
)
</script>

<template>
  <header class="page-header">
    <div class="page-header__main">
      <p class="page-header__eyebrow">{{ eyebrow }}</p>
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="description" class="page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.page-header__main {
  min-width: 0;
}
.page-header__eyebrow { margin: 0 0 10px; color: var(--lh-primary); font-size: 12px; font-weight: 600; line-height: 18px; letter-spacing: .12em; text-transform: uppercase; }

.page-header__title {
  margin: 0;
  color: var(--lh-text);
  font-size: 40px;
  font-weight: 700;
  line-height: 40px;
}

.page-header__description {
  margin: 8px 0 0;
  color: var(--lh-text-secondary);
  font-size: 14px;
  line-height: 22px;
}

.page-header__actions {
  display: flex;
  flex: none;
  align-items: center;
  gap: 8px;
}

@media (max-width: 767px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-header__title {
    font-size: 24px;
    line-height: 34px;
  }
}
</style>
