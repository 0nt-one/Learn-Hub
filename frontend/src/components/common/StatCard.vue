<script setup lang="ts">
import { computed } from 'vue'

/*
 * 指标卡：加载中、加载失败、未接入、真实数值必须是不同表达，
 * 不能把「没有数据」显示成 0（docs/ui-design-spec.md 5.1）。
 * 卡片表面复用 UCard，数值排版与状态文案留在这里。
 */
const props = withDefaults(
  defineProps<{
    label: string
    value?: string | number
    state?: 'ready' | 'loading' | 'unavailable' | 'error'
    icon?: string
    /** 覆盖默认提示，用来交代统计口径，例如「含停用课程」 */
    hint?: string
  }>(),
  { state: 'ready' },
)

const emit = defineEmits<{ retry: [] }>()

const formatter = new Intl.NumberFormat('zh-CN')

const display = computed(() => {
  if (props.state !== 'ready' || props.value === undefined) return '—'
  return typeof props.value === 'number' ? formatter.format(props.value) : props.value
})

const hintText = computed(() => {
  // 状态优先于统计口径：加载中/失败时先说状态，成功后才补充口径说明
  if (props.state === 'loading') return '正在获取数据'
  if (props.state === 'error') return '加载失败'
  if (props.state === 'unavailable') return '数据暂未接入'
  if (props.value === undefined) return props.hint ?? '暂无记录'
  return props.hint ?? ''
})
</script>

<template>
  <UCard :ui="{ body: 'p-5 sm:p-5' }">
    <div class="stat" :aria-busy="state === 'loading' ? 'true' : undefined">
      <div class="stat__head">
        <p class="stat__label">{{ label }}</p>
        <UIcon v-if="icon" :name="icon" class="stat__icon" aria-hidden="true" />
      </div>
      <p class="stat__value" :class="{ 'stat__value--empty': state !== 'ready' }">{{ display }}</p>
      <p v-if="hintText" class="stat__hint">
        {{ hintText }}
        <UButton
          v-if="state === 'error'"
          size="xs"
          variant="link"
          color="primary"
          class="stat__retry"
          @click="emit('retry')"
        >
          重试
        </UButton>
      </p>
    </div>
  </UCard>
</template>

<style scoped>
.stat {
  display: grid;
  gap: 8px;
}

.stat__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.stat__label {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 14px;
}

.stat__icon {
  width: 20px;
  height: 20px;
  color: var(--lh-text-secondary);
}

.stat__value {
  margin: 0;
  color: var(--lh-text);
  font-size: 32px;
  font-weight: 700;
  line-height: 40px;
  font-variant-numeric: tabular-nums;
}

.stat__value--empty {
  color: var(--lh-text-dimmed);
}

.stat__hint {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.stat__retry {
  padding: 0;
  vertical-align: baseline;
}

@media (max-width: 767px) {
  .stat__value {
    font-size: 28px;
    line-height: 36px;
  }
}
</style>
