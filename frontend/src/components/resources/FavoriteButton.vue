<script setup lang="ts">
import { computed } from 'vue'
import { useFavorites } from '../../composables/useFavorites'
const props = defineProps<{ resourceId: number; favorited: boolean; disabled?: boolean; compact?: boolean }>()
const favorites = useFavorites()
const toast = useToast()
const saved = computed(() => favorites.value(props.resourceId, props.favorited))
async function toggle() {
  try { await favorites.toggle(props.resourceId, props.favorited) }
  catch (cause) { toast.add({ title: '收藏操作失败', description: cause instanceof Error ? cause.message : '请稍后重试。', color: 'error' }) }
}
</script>
<template>
  <UButton
    :color="saved ? 'warning' : 'neutral'"
    :variant="saved ? 'soft' : 'outline'"
    :class="[ 'favorite-btn', { 'favorite--saved': saved } ]"
    :icon="saved ? 'i-lucide-bookmark-check' : 'i-lucide-bookmark'"
    :aria-label="saved ? '取消收藏' : '收藏资源'"
    :aria-pressed="saved"
    :title="saved ? '取消收藏' : '收藏资源'"
    :loading="favorites.pending.has(resourceId)"
    :disabled="disabled || favorites.pending.has(resourceId)"
    @click.stop="toggle"
    @keydown.stop
  >
    <template v-if="!compact">{{ saved ? '已收藏' : '收藏' }}</template>
  </UButton>
</template>

<style scoped>
/*
 * 收藏按钮在两态下都要有一圈可见的边框，否则叠在卡片装饰图形上会"糊"进去。
 * 用 box-shadow 而不是 border：UButton 的 outline/soft 变体本身用 ring（也是 box-shadow），
 * 直接覆盖它既能得到一致的 1px 边框，又不会和已有 ring 叠成双线。
 */
.favorite-btn {
  box-shadow: inset 0 0 0 1px var(--lh-control-track);
}

/* 已收藏：比 warning-soft 更淡的一层黄 + 暖色描边，避免整颗按钮显得发重 */
.favorite--saved {
  background-color: var(--lh-favorite-soft);
  color: var(--lh-favorite-text);
  box-shadow: inset 0 0 0 1px var(--lh-favorite-border);
}
</style>
