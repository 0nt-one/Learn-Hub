<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { listResourceReviews } from '../../api/reviews'
import { ApiError } from '../../api/client'
import { clearSession, useSession } from '../../api/session'
import type { Resource } from '../../types/resource'
import type { Review } from '../../types/review'
import EmptyState from '../common/EmptyState.vue'
import ErrorState from '../common/ErrorState.vue'

const open = defineModel<boolean>('open', { default: false })
const props = defineProps<{ resource: Pick<Resource, 'id' | 'title'> | null }>()
const { accessToken } = useSession()
const pageSize = 10
const page = ref(1)
const total = ref(0)
const items = ref<Review[]>([])
const loading = ref(false)
const error = ref('')
const requestId = ref('')
let sequence = 0

async function load() {
  const current = ++sequence
  items.value = []
  error.value = ''
  requestId.value = ''
  if (!open.value || !props.resource) { loading.value = false; return }
  loading.value = true
  try {
    const result = await listResourceReviews(props.resource.id, { page: page.value, page_size: pageSize })
    if (current !== sequence) return
    total.value = result.total
    const lastPage = Math.max(1, Math.ceil(result.total / pageSize))
    if (page.value > lastPage) { page.value = lastPage; return }
    items.value = result.items
  } catch (cause) {
    if (current !== sequence) return
    if (cause instanceof ApiError && cause.status === 401) { open.value = false; clearSession(); return }
    error.value = cause instanceof ApiError
      ? cause.status === 404 ? '资源不存在，或你没有查看该资源审核历史的权限。' : cause.message
      : '审核历史加载失败，请稍后重试。'
    requestId.value = cause instanceof ApiError ? cause.requestId : ''
  } finally { if (current === sequence) loading.value = false }
}
watch([open, () => props.resource?.id], () => {
  sequence++
  // 关闭时保留列表内容，否则退出动画会闪成一张空表
  if (!open.value) return
  items.value = []
  error.value = ''
  loading.value = false
  total.value = 0
  if (page.value !== 1) page.value = 1
  else void load()
}, { flush: 'sync' })
watch(page, () => { void load() })
watch(accessToken, () => { sequence++; open.value = false; items.value = []; total.value = 0 })
onUnmounted(() => { sequence++ })
function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '时间未知' : new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium', timeStyle: 'short', hour12: false,
  }).format(date)
}
</script>

<template>
  <UModal v-model:open="open" title="审核历史" :description="resource?.title"
    :ui="{ content: 'sm:max-w-2xl', description: 'break-words whitespace-normal', footer: 'justify-between gap-3 flex-wrap' }">
    <template #body>
      <div v-if="loading" class="space-y-4" role="status" aria-label="正在加载审核历史" aria-busy="true">
        <USkeleton v-for="n in 3" :key="n" class="h-28 w-full" />
      </div>
      <ErrorState v-else-if="error" :description="error" :request-id="requestId" @retry="load" />
      <EmptyState v-else-if="!items.length" centered icon="i-lucide-history" title="暂无审核记录" description="资源完成审核后，结果和审核意见会显示在这里。" />
      <div v-else class="history">
        <p class="history__hint">最新记录在前 · 时间按本地时区显示</p>
        <ol class="history__list">
          <li v-for="review in items" :key="review.id" class="history__record">
            <div class="history__heading">
              <UBadge :color="review.decision === 'approved' ? 'success' : 'error'" variant="soft"
                :icon="review.decision === 'approved' ? 'i-lucide-circle-check' : 'i-lucide-circle-x'">
                {{ review.decision === 'approved' ? '审核通过' : '已驳回' }}
              </UBadge>
              <time :datetime="review.created_at">{{ formatDate(review.created_at) }}</time>
            </div>
            <p class="history__meta">审核人 #{{ review.reviewer_id }}<span>资源版本 v{{ review.resource_version }}</span></p>
            <p class="history__label">审核意见</p>
            <p class="history__comment">{{ review.comment || '未填写审核意见' }}</p>
          </li>
        </ol>
      </div>
    </template>
    <template #footer>
      <span class="history__hint">共 {{ total }} 条记录</span>
      <UPagination v-if="total > pageSize" v-model:page="page" :total="total" :items-per-page="pageSize" :disabled="loading" :sibling-count="0" size="sm" />
      <UButton color="neutral" variant="outline" @click="open = false">关闭</UButton>
    </template>
  </UModal>
</template>

<style scoped>
.history { display: grid; gap: 16px; }
.history__hint { margin: 0; font-size: 12px; color: var(--lh-text-secondary); }
.history__list { display: grid; gap: 14px; list-style: none; margin: 0; padding: 0; }
.history__record { min-width: 0; padding: 18px; border: 1px solid var(--lh-border); border-radius: 12px; }
.history__heading { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.history__heading time, .history__meta { font-size: 12px; color: var(--lh-text-secondary); }
.history__meta { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 12px 0 16px; }
.history__label { margin: 0 0 6px; font-size: 12px; font-weight: 600; }
.history__comment { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 14px; line-height: 1.8; }
</style>
