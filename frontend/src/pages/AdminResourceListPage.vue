<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { listAdminResources } from '../api/resources'
import { listCourses } from '../api/courses'
import { listCategories } from '../api/categories'
import { ApiError } from '../api/client'
import { clearSession, useSession } from '../api/session'
import { usePagedOptions } from '../composables/usePagedOptions'
import AdminLayout from '../layouts/AdminLayout.vue'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import ResourceTypeBadge from '../components/resources/ResourceTypeBadge.vue'
import StatusBadge from '../components/resources/StatusBadge.vue'
import ResourceFilterPanel from '../components/resources/ResourceFilterPanel.vue'
import ReviewHistoryModal from '../components/resources/ReviewHistoryModal.vue'
import ResourceArchiveModal from '../components/resources/ResourceArchiveModal.vue'
import type { Resource, ResourceFilters, ResourceSort, ResourceStatus } from '../types/resource'

const { currentUser, accessToken } = useSession()
const allowed = computed(() => currentUser.value?.role === 'admin' && !!accessToken.value)
const items = ref<Resource[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const query = ref('')
const status = ref<'all' | ResourceStatus>('all')
const sort = ref<ResourceSort>('newest')
const blankFilters = (): ResourceFilters => ({ courseId: null, categoryId: null, type: null })
const filters = ref<ResourceFilters>(blankFilters())
const draft = ref<ResourceFilters>(blankFilters())
const filterOpen = ref(false)
const loading = ref(false)
const error = ref('')
const requestId = ref('')
const historyOpen = ref(false)
const archiveOpen = ref(false)
const selected = ref<Resource | null>(null)
let sequence = 0
const courses = usePagedOptions(p => listCourses({ page: p, page_size: 100 }), clearSession)
const categories = usePagedOptions(p => listCategories({ page: p, page_size: 100 }), clearSession)
const filterProps = computed(() => ({
  courses: courses.items.value, categories: categories.items.value,
  coursesMore: courses.more.value, categoriesMore: categories.more.value,
  coursesLoading: courses.loading.value, categoriesLoading: categories.loading.value,
  coursesError: courses.error.value, categoriesError: categories.error.value,
}))
const statuses = [
  { label: '全部状态', value: 'all' }, { label: '草稿', value: 'draft' },
  { label: '待审核', value: 'pending' }, { label: '已发布', value: 'approved' },
  { label: '已驳回', value: 'rejected' }, { label: '已归档', value: 'archived' },
]
const columns = [
  { accessorKey: 'title', header: '资源' },
  { accessorKey: 'course_title', header: '课程 / 分类', meta: { class: { th: 'w-[18%]' } } },
  { accessorKey: 'owner_display_name', header: '投稿人', meta: { class: { th: 'w-[90px]' } } },
  { accessorKey: 'status', header: '状态', meta: { class: { th: 'w-[100px]' } } },
  { accessorKey: 'updated_at', header: '更新时间', meta: { class: { th: 'w-[120px]' } } },
  { id: 'actions', header: '操作', meta: { class: { th: 'w-[240px]' } } },
]
const chips = computed(() => [
  ...(query.value ? [`标题：${query.value}`] : []),
  ...(filters.value.courseId ? [`课程：${courses.items.value.find(c => c.id === filters.value.courseId)?.title ?? `#${filters.value.courseId}`}`] : []),
  ...(filters.value.categoryId ? [`分类：${categories.items.value.find(c => c.id === filters.value.categoryId)?.name ?? `#${filters.value.categoryId}`}`] : []),
  ...(filters.value.type ? [{ document: '文档', video: '视频', link: '链接' }[filters.value.type]] : []),
])
async function load() {
  const seq = ++sequence
  error.value = ''; requestId.value = ''; items.value = []
  if (!allowed.value) { loading.value = false; return }
  loading.value = true
  try {
    const data = await listAdminResources({
      page: page.value, page_size: pageSize.value, q: query.value || undefined,
      status: status.value === 'all' ? undefined : status.value, sort: sort.value,
      course_id: filters.value.courseId ?? undefined,
      category_id: filters.value.categoryId ?? undefined, resource_type: filters.value.type ?? undefined,
    })
    if (seq !== sequence) return
    total.value = data.total
    const lastPage = Math.max(1, Math.ceil(data.total / pageSize.value))
    if (page.value > lastPage) { page.value = lastPage; return }
    items.value = data.items
  } catch (cause) {
    if (seq !== sequence) return
    total.value = 0
    if (cause instanceof ApiError && cause.status === 401) clearSession()
    else {
      error.value = cause instanceof ApiError ? cause.message : '资源加载失败，请重试。'
      requestId.value = cause instanceof ApiError ? cause.requestId : ''
    }
  } finally { if (seq === sequence) loading.value = false }
}
function search() {
  const next = keyword.value.trim().slice(0, 100)
  if (query.value === next) { if (page.value !== 1) page.value = 1; else void load() }
  else query.value = next
}
function reset() { keyword.value = ''; query.value = ''; status.value = 'all'; filters.value = blankFilters(); sort.value = 'newest' }
function showFilters() { draft.value = { ...filters.value }; filterOpen.value = true }
function applyFilters() { filters.value = { ...draft.value }; filterOpen.value = false }
function showHistory(resource: Resource) { selected.value = resource; historyOpen.value = true }
function showArchive(resource: Resource) { selected.value = resource; archiveOpen.value = true }
function externalUrl(value: string) {
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : undefined } catch { return undefined }
}
function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN').format(date)
}
watch([query, status, filters, sort, pageSize], () => { if (page.value !== 1) page.value = 1; else void load() })
watch(page, () => { void load() })
watch([accessToken, allowed], () => {
  sequence++; items.value = []; total.value = 0; loading.value = false
  historyOpen.value = false; archiveOpen.value = false; filterOpen.value = false; selected.value = null
  courses.reset(); categories.reset()
  if (allowed.value) {
    void courses.loadMore(); void categories.loadMore()
    if (page.value !== 1) page.value = 1; else void load()
  }
}, { immediate: true, flush: 'sync' })
onUnmounted(() => { sequence++ })
</script>

<template>
  <AdminLayout>
    <UAlert v-if="!allowed" color="warning" variant="soft" title="仅管理员可查看资源管理">
      <template #actions>
        <UButton v-if="!accessToken" to="/login">前往登录</UButton>
      </template>
    </UAlert>
    <template v-else>
      <form class="admin-resources__toolbar" @submit.prevent="search">
        <UInput v-model="keyword" class="admin-resources__search" icon="i-lucide-search" placeholder="搜索资源标题"
          aria-label="搜索资源标题" maxlength="100" />
        <UButton type="submit" :loading="loading">搜索</UButton>
        <USelect v-model="status" :items="statuses" aria-label="资源状态" class="w-32" />
        <USelect v-model="sort" :items="[{ label: '最新创建', value: 'newest' }, { label: '标题排序', value: 'title' }]"
          aria-label="排序" class="w-32" />
        <UButton color="neutral" variant="outline" icon="i-lucide-sliders-horizontal" @click="showFilters">更多筛选
        </UButton>
        <UButton color="neutral" variant="outline" icon="i-lucide-refresh-cw" :loading="loading" @click="load">刷新
        </UButton>
        <UButton color="neutral" variant="outline" icon="i-lucide-rotate-ccw" class="admin-resources__reset"
          @click="reset">重置筛选</UButton>
      </form>
      <div v-if="chips.length" class="admin-resources__chips">
        <UBadge v-for="chip in chips" :key="chip" variant="soft" class="max-w-full whitespace-normal break-all">{{ chip
          }}</UBadge>
      </div>
      <BaseCard density="compact">
        <ErrorState v-if="error" :description="error" :request-id="requestId" @retry="load" />
        <UTable v-else :data="items" :columns="columns" :loading="loading" caption="管理员资源列表" empty="没有符合条件的资源，请调整筛选条件。"
          :ui="{ base: 'w-full min-w-[1100px] table-fixed table-center', th: 'h-10 px-3 py-0 text-xs', td: 'px-3 py-3 text-sm text-default', tr: 'hover:bg-elevated/50' }">
          <template #title-cell="{ row }">
            <div class="admin-resources__title">
              <p :title="row.original.title">{{ row.original.title }}</p>
              <ResourceTypeBadge :type="row.original.resource_type" class="shrink-0" />
            </div>
            <p class="admin-resources__secondary" :title="row.original.description">{{ row.original.description ||
              '暂无描述' }}</p>
          </template>
          <template #course_title-cell="{ row }">
            <p class="truncate" :title="row.original.course_title">{{ row.original.course_title }}</p>
            <p class="admin-resources__secondary" :title="row.original.category_name">{{ row.original.category_name }}
            </p>
          </template>
          <template #owner_id-cell="{ row }"><span :title="`投稿人编号 ${row.original.owner_id}`">#{{ row.original.owner_id
              }}</span></template>
          <template #status-cell="{ row }">
            <StatusBadge :status="row.original.status" />
          </template>
          <template #updated_at-cell="{ row }">{{ formatDate(row.original.updated_at) }}</template>
          <template #actions-cell="{ row }">
            <div class="admin-resources__actions">
              <UButton v-if="externalUrl(row.original.url)" :to="externalUrl(row.original.url)" target="_blank"
                rel="noopener noreferrer" color="neutral" variant="ghost" size="sm" icon="i-lucide-external-link">查看
              </UButton>
              <UButton color="neutral" variant="ghost" size="sm" @click="showHistory(row.original)">审核历史</UButton>
              <UButton v-if="row.original.status !== 'archived'" color="error" variant="ghost" size="sm"
                @click="showArchive(row.original)">归档</UButton>
            </div>
          </template>
          <template #loading>
            <div role="status" aria-label="正在加载资源" class="space-y-3 py-5">
              <USkeleton v-for="n in 3" :key="n" class="h-5 w-full" />
            </div>
          </template>
        </UTable>
      </BaseCard>
      <div class="admin-resources__footer">
        <span>共 <strong class="admin-resources__count">{{ total }}</strong> 份资源</span>
        <UPagination v-if="total > pageSize" v-model:page="page" :items-per-page="pageSize" :total="total"
          :disabled="loading" size="sm" />
        <USelect v-model="pageSize" :items="[{ label: '20 条 / 页', value: 20 }, { label: '40 条 / 页', value: 40 }]"
          aria-label="每页数量" />
      </div>
    </template>
    <USlideover v-model:open="filterOpen" title="筛选资源" description="可选择全部课程和分类，包括已停用项。">
      <template #body>
        <ResourceFilterPanel v-model="draft" v-bind="filterProps" @reset="draft = blankFilters()"
          @load-courses="courses.loadMore" @load-categories="categories.loadMore" />
      </template>
      <template #footer>
        <UButton block @click="applyFilters">应用筛选</UButton>
      </template>
    </USlideover>
    <ReviewHistoryModal v-model:open="historyOpen" :resource="selected" />
    <ResourceArchiveModal v-model:open="archiveOpen" :resource="selected" @archived="load" @refresh="load" />
  </AdminLayout>
</template>

<style scoped>
.admin-resources__toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.admin-resources__search {
  flex: 1;
  min-width: 200px;
  max-width: 360px;
}

.admin-resources__reset {
  margin-left: auto;
}

.admin-resources__count {
  color: var(--lh-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.admin-resources__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.admin-resources__title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.admin-resources__title p {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin: 0;
  color: var(--lh-text);
  font-weight: 600;
}

.admin-resources__secondary {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--lh-text-secondary);
}

.admin-resources__actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
}

.admin-resources__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 20px;
  font-size: 13px;
  color: var(--lh-text-secondary);
}

@media (max-width: 767px) {
  .admin-resources__reset {
    margin-left: 0;
  }
}
</style>
