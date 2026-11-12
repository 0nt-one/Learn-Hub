<script setup lang="ts">
/*
 * 空/未接入状态统一走 Nuxt UI 的 UEmpty（variant="naked" 不带自己的边框，
 * 用于卡片内部）。默认左对齐，centered 用于整块居中的目录空状态。
 */
withDefaults(
  defineProps<{
    title: string
    description?: string
    icon?: string
    centered?: boolean
  }>(),
  { description: '', icon: 'i-lucide-circle-dashed' },
)
</script>

<template>
  <UEmpty
    variant="naked"
    :title="title"
    :description="description"
    :as="{ title: 'h3' }"
    :ui="{
      root: centered ? 'min-h-[104px] items-center justify-center gap-0 p-0 sm:p-0 lg:p-0' : 'min-h-[104px] items-stretch justify-center gap-0 p-0 sm:p-0 lg:p-0',
      header: centered ? 'max-w-none flex-col items-center gap-3 text-center' : 'max-w-none flex-row items-center gap-4 text-left',
      title: 'text-[15px] leading-6 font-semibold',
      description: centered ? 'text-center text-[13px] leading-5' : 'text-left text-[13px] leading-5',
    }"
  >
    <template #leading>
      <div class="empty-state__symbol" aria-hidden="true">
        <UIcon :name="icon" class="empty-state__icon" />
      </div>
    </template>
  </UEmpty>
</template>

<style scoped>
.empty-state__symbol {
  display: grid;
  flex: none;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: var(--radius-lg);
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
}

.empty-state__icon {
  width: 24px;
  height: 24px;
}
</style>
