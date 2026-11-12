<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { listOperationLogs, type OperationLog } from '../api/operationLogs'
import { useSession } from '../api/session'
import AdminLayout from '../layouts/AdminLayout.vue'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import { ACTION_COLORS, ACTION_LABELS, TARGET_LABELS, targetLabel } from '../constants/operationLog'

const { accessToken, currentUser } = useSession()
const toast = useToast()
const allowed = computed(() => !!accessToken.value && currentUser.value?.role === 'admin')
const empty = () => ({ actor_id: '', action: '', target_type: 'all', target_id: '', created_from: '', created_to: '' })
const draft = reactive(empty())
let filters: Record<string, string> = {}
const items = ref<OperationLog[]>([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const error = ref('')
const requestId = ref('')
const filterError = ref('')
let sequence = 0
const targets = [
  { label: '全部对象', value: 'all' },
  ...Object.entries(TARGET_LABELS).map(([value, label]) => ({ label, value })),
]
/*
 * 列宽固定，避免浏览器按内容自动分配：request_id 是 36 位 UUID，
 * 自动布局会把摘要列挤成一条缝。摘要列吃掉剩余宽度并截断，靠 title 看全文。
 */
const columns = [
  { accessorKey: 'created_at', header: '操作时间', meta: { class: { th: 'w-[150px]', td: 'whitespace-nowrap text-muted tabular-nums' } } },
  { accessorKey: 'actor_id', header: '操作人', meta: { class: { th: 'w-[84px]', td: 'whitespace-nowrap' } } },
  { accessorKey: 'action', header: '操作', meta: { class: { th: 'w-[132px]' } } },
  { accessorKey: 'target_type', header: '操作对象', meta: { class: { th: 'w-[124px]', td: 'whitespace-nowrap' } } },
  // 摘要吃掉剩余宽度：它才是内容最长、最需要空间的一列
  { accessorKey: 'summary', header: '摘要', meta: { class: { th: '' } } },
  { accessorKey: 'request_id', header: '请求编号', meta: { class: { th: 'w-[320px]' } } },
]
const dateFormat = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'medium' })

async function copyRequestId(id: string) {
  try {
    await navigator.clipboard.writeText(id)
    toast.add({ title: '已复制请求编号', color: 'success' })
  } catch {
    toast.add({ title: '复制失败', description: '可以选中完整编号手动复制。', color: 'error' })
  }
}

async function load(next = page.value) {
  if (!allowed.value) return
  const current = ++sequence
  loading.value = true
  error.value = ''
  requestId.value = ''
  items.value = []
  try {
    const data = await listOperationLogs(next, filters)
    if (current !== sequence) return
    page.value = data.page
    total.value = data.total
    items.value = data.items
  } catch (cause) {
    if (current !== sequence) return
    error.value = cause instanceof Error ? cause.message : '操作日志加载失败，请重试。'
    requestId.value = cause instanceof ApiError ? cause.requestId : ''
  } finally {
    if (current === sequence) loading.value = false
  }
}

function applyFilters() {
  filterError.value = ''
  const next: Record<string, string> = {}
  for (const [key, raw] of Object.entries(draft)) {
    const value = raw.trim()
    if (!value || (key === 'target_type' && value === 'all')) continue
    if (key === 'actor_id' || key === 'target_id') {
      if (!/^\d+$/.test(value) || Number(value) < 1 || !Number.isSafeInteger(Number(value))) {
        filterError.value = '操作人和对象编号必须为正整数。'
        return
      }
    }
    if (key === 'created_from' || key === 'created_to') {
      const date = new Date(value)
      if (!Number.isFinite(date.getTime())) {
        filterError.value = '请输入有效的日期和时间。'
        return
      }
      next[key] = date.toISOString()
    } else next[key] = value
  }
  if (next.created_from && next.created_to && next.created_from > next.created_to) {
    filterError.value = '开始时间不能晚于结束时间。'
    return
  }
  filters = next
  page.value = 1
  void load()
}

function reset() {
  Object.assign(draft, empty())
  applyFilters()
}

watch([accessToken, allowed], () => {
  sequence++
  items.value = []
  total.value = 0
  loading.value = false
  error.value = ''
  reset()
}, { immediate: true })
onUnmounted(() => { sequence++ })
</script>

<template>
  <AdminLayout>
    <UAlert v-if="!allowed" color="warning" variant="soft" title="仅管理员可查看操作日志。" />
    <template v-else>
      <form class="log-filters" @submit.prevent="applyFilters">
        <label>操作人编号<UInput v-model="draft.actor_id" inputmode="numeric" placeholder="例如 12" /></label>
        <label>操作名称<UInput v-model="draft.action" maxlength="64" placeholder="例如 resource.archive" /></label>
        <label>对象类型<USelect v-model="draft.target_type" :items="targets" /></label>
        <label>对象编号<UInput v-model="draft.target_id" inputmode="numeric" /></label>
        <label>开始时间（本地，包含）<UInput v-model="draft.created_from" type="datetime-local" /></label>
        <label>结束时间（本地，不含）<UInput v-model="draft.created_to" type="datetime-local" /></label>
        <div class="log-filters__actions">
          <UButton type="submit" :loading="loading">查询</UButton>
          <UButton type="button" color="neutral" variant="outline" @click="reset">重置</UButton>
        </div>
      </form>
      <UAlert v-if="filterError" class="mb-4" color="error" variant="soft" :title="filterError" />
      <BaseCard density="compact">
        <ErrorState v-if="error" :description="error" :request-id="requestId" @retry="load()" />
        <UTable v-else class="log-table" :data="items" :columns="columns" :loading="loading" empty="没有符合条件的操作日志。"
          :ui="{ base: 'w-full min-w-[1000px] table-fixed', td: 'align-middle py-2' }">
          <template #created_at-cell="{ row }">{{ dateFormat.format(new Date(row.original.created_at)) }}</template>
          <template #actor_id-cell="{ row }"><span class="text-muted">#{{ row.original.actor_id }}</span></template>
          <template #action-cell="{ row }">
            <UBadge :color="ACTION_COLORS[row.original.action] ?? 'neutral'" variant="subtle" size="sm">
              {{ ACTION_LABELS[row.original.action] ?? row.original.action }}
            </UBadge>
          </template>
          <template #target_type-cell="{ row }">
            <span class="text-muted">{{ targetLabel(row.original.target_type) }} #{{ row.original.target_id }}</span>
          </template>
          <template #summary-cell="{ row }">
            <p class="line-clamp-2 max-w-[520px] break-words" :title="row.original.summary">
              {{ row.original.summary || '—' }}
            </p>
          </template>
          <template #request_id-cell="{ row }">
            <div v-if="row.original.request_id" class="flex items-center gap-2">
              <code class="min-w-0 select-all break-all whitespace-normal text-xs text-muted">{{ row.original.request_id }}</code>
              <UButton type="button" icon="i-lucide-copy" size="xs" color="neutral" variant="ghost"
                class="shrink-0" aria-label="复制请求编号" title="复制请求编号" @click="copyRequestId(row.original.request_id)" />
            </div>
            <span v-else>—</span>
          </template>
        </UTable>
      </BaseCard>
      <div v-if="!error" class="table-footer">
        <p class="table-footer__total">共 <span class="table-footer__count">{{ total }}</span> 条日志</p>
        <UPagination v-if="total > 20" :page="page" :total="total" :items-per-page="20" :disabled="loading"
          size="sm" @update:page="load" />
      </div>
    </template>
  </AdminLayout>
</template>

<style scoped>
.log-filters { display: flex; flex-wrap: wrap; align-items: end; gap: 12px; margin-bottom: 16px; }
.log-filters label { display: grid; gap: 6px; color: var(--lh-text-secondary); font-size: 13px; }
.log-filters__actions { display: flex; gap: 8px; }

/*
 * table-fixed 只决定列宽怎么分，表格自身的宽度仍取决于 width。
 * 这里同时覆盖外层容器和 table 元素，避免卡片变宽后在右侧留白。
 */
.log-table,
.log-table :deep(table) {
  width: 100%;
}

/* 与其他管理表格页保持一致（AdminUsersPage / AdminCategoriesPage 等同一套） */
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
}

.table-footer__total {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

/* 数字用主题色突出，其余文字保持次要色 */
.table-footer__count {
  color: var(--lh-primary);
  font-weight: 600;
}
</style>
