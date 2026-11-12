<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { listCourses } from '../api/courses'
import { listMyResources, submitResource, withdrawResource } from '../api/resources'
import { clearSession, useSession } from '../api/session'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import ResourceTypeBadge from '../components/resources/ResourceTypeBadge.vue'
import ResourceFormModal from '../components/resources/ResourceFormModal.vue'
import ReviewHistoryModal from '../components/resources/ReviewHistoryModal.vue'
import ResourceArchiveModal from '../components/resources/ResourceArchiveModal.vue'
import StatusBadge from '../components/resources/StatusBadge.vue'
import TeacherLayout from '../layouts/TeacherLayout.vue'
import type { Resource, ResourceStatus } from '../types/resource'

/*
 * 我的资源：GET /resources/mine，含草稿在内的全部状态。
 * 资源响应直接包含课程和分类名称；课程负责人（别人负责的课程）另外用
 * GET /courses 的字典补上，只有不是本人时才显示，避免每行都挂自己的名字。
 */
const PAGE_SIZE = 20

const { currentUser, accessToken } = useSession()
const toast = useToast()
let active = true
let loadSequence = 0

const items = ref<Resource[]>([])
const total = ref(0)
const page = ref(1)
const statusFilter = ref<'all' | ResourceStatus>('all')
const createOpen = ref(false)
const editOpen = ref(false)
const editingResource = ref<Resource | null>(null)
const historyResource = ref<Resource | null>(null)
const historyOpen = ref(false)
function showHistory(resource: Resource) { historyResource.value = resource; historyOpen.value = true }
const submittingId = ref<number | null>(null)
const actionError = ref('')
const archiveOpen = ref(false)
const archiveTarget = ref<Resource | null>(null)
function canArchive(resource: Resource) {
  return resource.status !== 'archived' && (currentUser.value?.role === 'admin' ||
    (resource.owner_id === currentUser.value?.id && resource.status !== 'pending'))
}
function showArchive(resource: Resource) {
  if (!canArchive(resource)) return
  archiveTarget.value = resource
  archiveOpen.value = true
}
const withdrawOpen = ref(false)
const withdrawing = ref(false)
const withdrawTarget = ref<Resource | null>(null)
const withdrawError = ref('')
const withdrawConflict = ref(false)

function canWithdraw(resource: Resource) {
  return resource.owner_id === currentUser.value?.id && ['pending', 'approved'].includes(resource.status)
}
function openWithdraw(resource: Resource) {
  if (!canWithdraw(resource) || withdrawing.value) return
  withdrawTarget.value = resource
  withdrawError.value = ''
  withdrawConflict.value = false
  withdrawOpen.value = true
}
async function confirmWithdraw() {
  const resource = withdrawTarget.value
  if (!resource || withdrawing.value || withdrawConflict.value) return
  const token = accessToken.value
  withdrawing.value = true
  withdrawError.value = ''
  try {
    const updated = await withdrawResource(resource.id, resource.version_id)
    if (!active || token !== accessToken.value) return
    items.value = items.value.map(item => item.id === updated.id ? updated : item)
    withdrawOpen.value = false
    toast.add({ title: '资源已撤回', description: '已恢复为草稿，可以修改后重新提交审核。', color: 'success' })
    await load()
  } catch (cause) {
    if (!active || token !== accessToken.value) return
    if (cause instanceof ApiError && cause.status === 401) { clearSession(); return }
    withdrawConflict.value = cause instanceof ApiError && [403, 404, 409].includes(cause.status)
    withdrawError.value = cause instanceof ApiError
      ? cause.code === 'VERSION_CONFLICT' ? '资源已被修改，请刷新列表后重新确认撤回。'
        : cause.code === 'INVALID_STATE' ? '资源状态已变化，当前不能撤回，请刷新列表。'
          : cause.message
      : '撤回失败，请稍后重试。'
  } finally { if (active && token === accessToken.value) withdrawing.value = false }
}
function refreshAfterConflict() { withdrawOpen.value = false; void load() }
watch(accessToken, () => {
  loadSequence++
  withdrawOpen.value = false
  withdrawTarget.value = null
  withdrawing.value = false
  items.value = []
  total.value = 0
}, { flush: 'sync' })
onUnmounted(() => { active = false; loadSequence++ })

/** 后端只允许 draft / rejected 状态下修改；其它状态直接不显示「修改」按钮 */
function canEdit(resource: Resource): boolean {
  return resource.status === 'draft' || resource.status === 'rejected'
}

function openEdit(resource: Resource): void {
  editingResource.value = resource
  editOpen.value = true
}

/** 草稿和被驳回的资源可以送审；提交成功后状态变 pending */
function canSubmitForReview(resource: Resource): boolean {
  return canEdit(resource)
}

async function submitForReview(resource: Resource): Promise<void> {
  actionError.value = ''
  submittingId.value = resource.id

  try {
    const updated = await submitResource(resource.id, resource.version_id)
    items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (e) {
    if (e instanceof ApiError) {
      if (e.code === 'VERSION_CONFLICT') {
        actionError.value = '这条资源刚被修改过，请刷新后再提交。'
      } else if (e.code === 'REFERENCE_INACTIVE') {
        actionError.value = '所属课程或分类已停用，无法提交审核。'
      } else {
        actionError.value = e.message
      }
    } else {
      actionError.value = '提交审核失败，请稍后重试。'
    }
  } finally {
    submittingId.value = null
  }
}

/** course_id → 负责人 id / 显示名，仅用于标注"别人的课程" */
const courseOwners = ref<Record<number, { id: number; name: string }>>({})

const status = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')


const STATUS_FILTERS: { value: 'all' | ResourceStatus; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已发布' },
  { value: 'rejected', label: '已驳回' },
  { value: 'archived', label: '已归档' },
]

const columns = computed(() => [
  { accessorKey: 'title', header: '资源' },
  { accessorKey: 'course_id', header: '归属', meta: { class: { th: 'w-[24%]' } } },
  { accessorKey: 'status', header: '状态', meta: { class: { th: 'w-[120px]', td: 'w-[120px]' } } },
  {
    accessorKey: 'updated_at',
    header: '更新时间',
    meta: { class: { th: 'w-[140px]', td: 'w-[140px]' } },
  },
  {
    id: 'actions',
    header: '操作',
    meta: { class: { th: 'w-[260px]' } },
  },
])

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(date)
}

async function loadCourseOwners(): Promise<void> {
  try {
    const data = await listCourses({ page: 1, page_size: 100 })
    courseOwners.value = Object.fromEntries(
      data.items.map((course) => [
        course.id,
        { id: course.teacher_id, name: course.teacher_display_name },
      ]),
    )
  } catch {
    // 拿不到就只显示课程名，不影响列表本身
  }
}

/** 别人负责的课程才返回 @负责人，自己的返回空字符串 */
function ownerTag(courseId: number): string {
  const owner = courseOwners.value[courseId]
  if (!owner || owner.id === currentUser.value?.id) return ''
  return `@${owner.name}`
}

/** 归属第一行：课程名（必要时追加 @负责人）；字段缺失时退回 ID，不留空白 */
function courseLine(resource: Resource): string {
  const title = resource.course_title || `课程 #${resource.course_id}`
  const tag = ownerTag(resource.course_id)
  return tag ? `${title} ${tag}` : title
}

/** 归属第二行：分类名，缺失时退回 ID */
function categoryLine(resource: Resource): string {
  return resource.category_name || `分类 #${resource.category_id}`
}

async function load(): Promise<void> {
  const seq = ++loadSequence
  status.value = 'loading'

  try {
    const data = await listMyResources({
      page: page.value,
      page_size: PAGE_SIZE,
      status: statusFilter.value === 'all' ? null : statusFilter.value,
    })
    if (!active || seq !== loadSequence) return
    const lastPage = Math.max(1, Math.ceil(data.total / PAGE_SIZE))
    if (page.value > lastPage) { page.value = lastPage; await load(); return }
    items.value = data.items
    total.value = data.total
    status.value = 'ready'
  } catch (e) {
    if (!active || seq !== loadSequence) return
    loadError.value = e instanceof ApiError ? e.message : '加载失败，请稍后重试。'
    status.value = 'error'
  }
}

function onPageChange(next: number): void {
  page.value = next
  void load()
}

/** 新建成功后回到第一页（新草稿按创建时间倒序，在第一页） */
function onSaved(resource: Resource, mode: 'create' | 'edit'): void {
  if (mode === 'create') {
    page.value = 1
    void load()
    return
  }
  // 编辑成功：直接用返回的最新对象替换那一行（含新的 version_id）
  items.value = items.value.map((item) => (item.id === resource.id ? resource : item))
}

watch(statusFilter, () => {
  page.value = 1
  void load()
})

onMounted(() => {
  void loadCourseOwners()
  void load()
})
</script>

<template>
  <TeacherLayout>
    <div class="toolbar page-toolbar">
      <div class="toolbar__filters">
        <USelect
          v-model="statusFilter"
          :items="STATUS_FILTERS"
          size="lg"
          aria-label="按状态筛选"
          class="toolbar__select"
        />
        <UButton
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-refresh-cw"
          :loading="status === 'loading'"
          @click="load"
        >
          刷新
        </UButton>
      </div>
      <UButton
        class="toolbar__primary"
        color="primary"
        size="lg"
        icon="i-lucide-square-plus"
        @click="createOpen = true"
      >
        共享新资源
      </UButton>
    </div>

    <UAlert
      v-if="actionError"
      color="error"
      variant="soft"
      icon="i-lucide-circle-alert"
      :title="actionError"
      class="action-error"
    />

    <BaseCard density="compact">
      <ErrorState v-if="status === 'error'" :description="loadError" @retry="load" />

      <UTable
        v-else
        :data="items"
        :columns="columns"
        :loading="status === 'loading'"
        caption="我的资源"
        empty="还没有资源，点右上角「共享新资源」投稿第一份。"
        :ui="{
          base: 'w-full min-w-[1000px] table-fixed table-center',
          th: 'h-10 px-3 py-0 text-xs',
          td: 'h-14 px-3 py-0 text-sm text-default',
          tr: 'hover:bg-elevated/50',
        }"
      >
        <template #title-cell="{ row }">
          <div class="resource-cell">
            <div class="resource-cell__head">
              <p class="resource-cell__title" :title="row.original.title">{{ row.original.title }}</p>
              <ResourceTypeBadge class="shrink-0" :type="row.original.resource_type" />
            </div>
            <p class="resource-cell__desc" :title="row.original.description || '暂无描述'">{{ row.original.description || '暂无描述' }}</p>
          </div>
        </template>

        <template #course_id-cell="{ row }">
          <p class="owner-cell">{{ courseLine(row.original) }}</p>
          <p class="owner-cell__sub">{{ categoryLine(row.original) }}</p>
        </template>

        <template #status-cell="{ row }">
          <StatusBadge :status="row.original.status" />
        </template>

        <template #updated_at-cell="{ row }">
          <span class="date-cell">{{ formatDate(row.original.updated_at) }}</span>
        </template>

        <template #actions-cell="{ row }">
          <div class="actions">
            <UButton v-if="canArchive(row.original)" color="error" variant="ghost" size="sm" icon="i-lucide-archive" :disabled="submittingId !== null || withdrawing" @click="showArchive(row.original)">归档</UButton>
            <UButton v-if="canWithdraw(row.original)" color="warning" variant="ghost" size="sm" icon="i-lucide-undo-2" :loading="withdrawing" @click="openWithdraw(row.original)">撤回</UButton>
            <UButton color="neutral" variant="ghost" size="sm" icon="i-lucide-history" @click="showHistory(row.original)">审核历史</UButton>
            <UButton
              v-if="canSubmitForReview(row.original)"
              color="primary"
              variant="soft"
              size="sm"
              icon="i-lucide-send"
              :loading="submittingId === row.original.id"
              @click="submitForReview(row.original)"
            >
              提交审核
            </UButton>
            <UButton
              v-if="canEdit(row.original)"
              color="neutral"
              variant="ghost"
              size="sm"
              icon="i-lucide-pencil"
              @click="openEdit(row.original)"
            >
              修改
            </UButton>
            <UButton
              :to="row.original.url"
              target="_blank"
              rel="noopener noreferrer"
              color="neutral"
              variant="ghost"
              size="sm"
              icon="i-lucide-external-link"
            >
              打开
            </UButton>
          </div>
        </template>

        <template #loading>
          <div class="loading-stack">
            <USkeleton class="h-4 w-56" />
            <USkeleton class="h-4 w-44" />
            <USkeleton class="h-4 w-52" />
          </div>
        </template>
      </UTable>
    </BaseCard>

    <div class="table-footer">
      <p class="table-footer__total">共 <span class="table-footer__count">{{ total }}</span> 份资源</p>
      <UPagination
        v-if="total > PAGE_SIZE"
        :page="page"
        :total="total"
        :items-per-page="PAGE_SIZE"
        size="sm"
        @update:page="onPageChange"
      />
    </div>

    <ResourceFormModal v-model:open="createOpen" @saved="onSaved" />
    <ResourceArchiveModal v-model:open="archiveOpen" :resource="archiveTarget" @archived="load" @refresh="load" />
    <UModal v-model:open="withdrawOpen" title="撤回资源" :description="withdrawTarget?.title"
      :dismissible="!withdrawing" :close="!withdrawing" :ui="{ description: 'whitespace-normal break-words', footer: 'justify-end gap-3' }">
      <template #body>
        <div class="space-y-4 text-sm leading-7">
          <p>{{ withdrawTarget?.status === 'approved' ? '撤回后，资源将从公开资源目录中下架。' : '撤回后，资源将退出待审核队列。' }}资源会恢复为草稿，可以修改后重新提交审核，已有审核记录保留。</p>
          <UAlert v-if="withdrawError" color="error" variant="soft" :title="withdrawError" />
        </div>
      </template>
      <template #footer>
        <UButton color="neutral" variant="outline" :disabled="withdrawing" @click="withdrawOpen = false">取消</UButton>
        <UButton v-if="withdrawConflict" @click="refreshAfterConflict">刷新列表</UButton>
        <UButton v-else color="warning" :loading="withdrawing" @click="confirmWithdraw">确认撤回</UButton>
      </template>
    </UModal>
    <ReviewHistoryModal v-model:open="historyOpen" :resource="historyResource" />
    <ResourceFormModal v-model:open="editOpen" :resource="editingResource" @saved="onSaved" />
  </TeacherLayout>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.toolbar__filters {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.toolbar__filters > * {
  flex: none;
  white-space: nowrap;
}

.toolbar__primary {
  flex: none;
  margin-left: auto;
  white-space: nowrap;
}

.toolbar__select {
  width: 150px;
}

.resource-cell {
  min-width: 0;
}

.resource-cell__head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.resource-cell__title {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  color: var(--lh-text);
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.resource-cell__desc {
  margin: 0;
  overflow: hidden;
  color: var(--lh-text-secondary);
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.owner-cell {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin: 0;
  color: var(--lh-text);
  font-size: 13px;
  line-height: 20px;
}

.owner-cell__sub {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.date-cell {
  color: var(--lh-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.actions {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: center;
  padding: 8px 0;
  align-items: center;
  gap: 4px;
}

.loading-stack {
  display: grid;
  gap: 10px;
  justify-items: center;
  padding: 8px 0;
}

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

.table-footer__count {
  color: var(--lh-primary);
  font-weight: 600;
}

@media (max-width: 767px) {
  .toolbar {
    flex-wrap: wrap;
  }

  .toolbar__filters {
    flex-wrap: wrap;
    width: 100%;
  }

  .toolbar__primary,
  .toolbar__select {
    width: 100%;
  }
}
</style>
