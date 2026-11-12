<script setup lang="ts">
import { computed } from 'vue'

/*
 * 卡片表面统一走 Nuxt UI 的 UCard：边框、背景、圆角与分隔线都由主题令牌决定。
 * 这里只补充页面需要的「眉标 + 标题 + 右侧动作」头部结构和密度差异。
 */
const props = withDefaults(
  defineProps<{
    density?: 'comfortable' | 'compact'
    variant?: 'outline' | 'soft' | 'subtle'
    /** 卡片标题字号：后台用 sm(16)，展示型页面用 md(18) */
    titleSize?: 'sm' | 'md'
  }>(),
  { density: 'comfortable', variant: 'outline', titleSize: 'sm' },
)

const ui = computed(() => {
  const padding = props.density === 'compact' ? 'p-4 sm:p-4' : 'p-4 sm:p-6'
  return {
    header: padding,
    body: padding,
    footer: padding,
  }
})
</script>

<template>
  <UCard :variant="variant" :ui="ui">
    <template v-if="$slots.eyebrow || $slots.title || $slots.action" #header>
      <div class="base-card__heading">
        <div class="base-card__heading-main">
          <p v-if="$slots.eyebrow" class="base-card__eyebrow">
            <slot name="eyebrow" />
          </p>
          <div
            v-if="$slots.title"
            class="base-card__title"
            :class="{ 'base-card__title--md': titleSize === 'md' }"
          >
            <slot name="title" />
          </div>
        </div>
        <slot name="action" />
      </div>
    </template>

    <slot />

    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </UCard>
</template>

<style scoped>
.base-card__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.base-card__heading-main {
  min-width: 0;
}

.base-card__eyebrow {
  margin: 0 0 4px;
  color: var(--lh-primary);
  font-size: 12px;
  font-weight: 700;
}

.base-card__title :deep(h2),
.base-card__title :deep(h3) {
  margin: 0;
  color: var(--lh-text);
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
}

.base-card__title--md :deep(h2),
.base-card__title--md :deep(h3) {
  font-size: 18px;
  line-height: 26px;
}
</style>
