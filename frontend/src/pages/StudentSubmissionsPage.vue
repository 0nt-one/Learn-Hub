<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { listMyResources, submitResource, withdrawResource } from '../api/resources'
import { useSession } from '../api/session'
import StudentLayout from '../layouts/StudentLayout.vue'
import PageHero from '../components/common/PageHero.vue'
import PageHeader from '../components/common/PageHeader.vue'
import ErrorState from '../components/common/ErrorState.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ResourceTypeBadge from '../components/resources/ResourceTypeBadge.vue'
import StatusBadge from '../components/resources/StatusBadge.vue'
import ResourceFormModal from '../components/resources/ResourceFormModal.vue'
import ReviewHistoryModal from '../components/resources/ReviewHistoryModal.vue'
import ResourceArchiveModal from '../components/resources/ResourceArchiveModal.vue'
import ResourceDetailModal from '../components/resources/ResourceDetailModal.vue'
import type { Resource, ResourceStatus } from '../types/resource'

const pageSize = 20
const { accessToken, currentUser } = useSession()
const toast = useToast()
const items = ref<Resource[]>([])
const page = ref(1)
const total = ref(0)
const filter = ref<ResourceStatus | 'all'>('all')
const loading = ref(false)
const error = ref('')
const busy = ref(false)
const formOpen = ref(false)
const editTarget = ref<Resource | null>(null)
const historyOpen = ref(false)
const archiveOpen = ref(false)
const withdrawOpen = ref(false)
const detailOpen = ref(false)
const target = ref<Resource | null>(null)
let sequence = 0
let active = true

const statuses = [
  { value: 'all', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已发布' },
  { value: 'rejected', label: '已驳回' },
  { value: 'archived', label: '已归档' },
]
const dateFormat = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' })

async function load(next = page.value) {
  const current = ++sequence
  if (!accessToken.value) return
  loading.value = true
  error.value = ''
  page.value = next
  try {
    const result = await listMyResources({
      page: next,
      page_size: pageSize,
      status: filter.value === 'all' ? null : filter.value,
    })
    if (current !== sequence) return
    const lastPage = Math.max(1, Math.ceil(result.total / pageSize))
    if (next > lastPage) {
      await load(lastPage)
      return
    }
    items.value = result.items
    total.value = result.total
  } catch (cause) {
    if (current === sequence) error.value = cause instanceof Error ? cause.message : '投稿加载失败。'
  } finally {
    if (current === sequence) loading.value = false
  }
}

function showForm(resource: Resource | null = null) {
  editTarget.value = resource
  formOpen.value = true
}

function onCreated() {
  if (filter.value !== 'all' && filter.value !== 'draft') {
    filter.value = 'all'
    return
  }
  void load(1)
}

function onSaved(_resource: Resource, mode: 'create' | 'edit') {
  if (mode === 'create') onCreated()
  else void load()
}

function show(resource: Resource, panel: 'history' | 'archive' | 'withdraw' | 'detail') {
  target.value = resource
  const panels = { history: historyOpen, archive: archiveOpen, withdraw: withdrawOpen, detail: detailOpen }
  panels[panel].value = true
}

async function changeStatus(resource: Resource, action: 'submit' | 'withdraw') {
  if (busy.value || !accessToken.value || resource.owner_id !== currentUser.value?.id) return
  const token = accessToken.value
  busy.value = true
  try {
    const change = action === 'submit' ? submitResource : withdrawResource
    await change(resource.id, resource.version_id)
    if (!active || token !== accessToken.value) return
    withdrawOpen.value = false
    toast.add({ title: action === 'submit' ? '已提交审核' : '已撤回为草稿', color: 'success' })
    await load()
  } catch (cause) {
    if (!active || token !== accessToken.value) return
    if (cause instanceof ApiError && [403, 404, 409].includes(cause.status)) {
      withdrawOpen.value = false
      await load()
    }
    toast.add({ title: '操作失败', description: cause instanceof Error ? cause.message : '请稍后重试。', color: 'error' })
  } finally {
    if (token === accessToken.value) busy.value = false
  }
}

function moreActions(resource: Resource) {
  const actions = []
  if (resource.status === 'rejected') {
    actions.push({ label: '修改资源', icon: 'i-lucide-pencil', onSelect: () => showForm(resource) })
  }
  if (resource.status === 'draft' || resource.status === 'approved') {
    actions.push({ label: '审核历史', icon: 'i-lucide-history', onSelect: () => show(resource, 'history') })
  }
  if (resource.status === 'pending' || resource.status === 'approved') {
    actions.push({ label: '撤回为草稿', icon: 'i-lucide-undo-2', onSelect: () => show(resource, 'withdraw') })
  }
  if (resource.status !== 'pending' && resource.status !== 'archived') {
    actions.push({ label: '归档', icon: 'i-lucide-archive', onSelect: () => show(resource, 'archive') })
  }
  return actions
}

watch(filter, () => { void load(1) })
watch(accessToken, () => {
  items.value = []
  total.value = 0
  loading.value = false
  busy.value = false
  formOpen.value = historyOpen.value = archiveOpen.value = withdrawOpen.value = detailOpen.value = false
  target.value = editTarget.value = null
  void load(1)
}, { immediate: true, flush: 'sync' })
onUnmounted(() => { active = false; sequence++ })
</script>

<template>
  <StudentLayout @resource-shared="onCreated">
    <PageHero>
      <PageHeader eyebrow="My Submissions" title="我的投稿" description="分享学习资源，跟踪审核进度。" />
    </PageHero>
    <div class="submissions-toolbar">
      <USelect v-model="filter" :items="statuses" aria-label="筛选投稿状态" />
      <UButton icon="i-lucide-plus" @click="showForm()">分享资源</UButton>
    </div>
    <p class="submissions-count">共 <strong>{{ total }}</strong> 条投稿</p>
    <ErrorState v-if="error" :description="error" @retry="load()" />
    <div v-else-if="loading" role="status" aria-label="正在加载投稿" class="space-y-3">
      <USkeleton v-for="n in 3" :key="n" class="h-24 w-full rounded-xl" />
    </div>
    <UCard v-else-if="!items.length">
      <EmptyState centered icon="i-lucide-file-up" :title="filter === 'all' ? '还没有投稿' : '没有此状态的投稿'" />
      <div class="mt-4 flex justify-center">
        <UButton v-if="filter === 'all'" @click="showForm()">分享资源</UButton>
        <UButton v-else variant="outline" @click="filter = 'all'">查看全部</UButton>
      </div>
    </UCard>
    <ul v-else class="submissions-list">
      <li v-for="item in items" :key="item.id" class="submission">
        <div class="submission__info">
          <div class="submission__title">
            <ResourceTypeBadge class="shrink-0" :type="item.resource_type" />
            <h2 class="truncate font-semibold" :title="item.title">{{ item.title }}</h2>
          </div>
          <p class="truncate text-sm text-muted">{{ item.course_title || ('课程 #' + item.course_id) }} · 更新于 {{ dateFormat.format(new Date(item.updated_at)) }}</p>
        </div>
        <StatusBadge :status="item.status" />
        <div class="submission__actions">
          <UButton v-if="item.status === 'draft'" size="sm" color="neutral" variant="outline" :disabled="busy" @click="showForm(item)">继续编辑</UButton>
          <UButton v-if="item.status === 'draft' || item.status === 'rejected'" size="sm" :disabled="busy" @click="changeStatus(item, 'submit')">提交审核</UButton>
          <UButton v-if="item.status === 'approved'" size="sm" variant="soft" :disabled="busy" @click="show(item, 'detail')">查看资源</UButton>
          <UButton v-if="item.status !== 'draft' && item.status !== 'approved'" size="sm" variant="soft" :disabled="busy" @click="show(item, 'history')">
            {{ item.status === 'rejected' ? '查看驳回原因' : '审核历史' }}
          </UButton>
          <UDropdownMenu v-if="item.status !== 'archived'" :items="moreActions(item)">
            <UButton size="sm" color="neutral" variant="ghost" icon="i-lucide-ellipsis" aria-label="更多投稿操作" :disabled="busy" />
          </UDropdownMenu>
        </div>
      </li>
    </ul>
    <div v-if="!error && total > pageSize" class="mt-5 flex justify-center">
      <UPagination :page="page" :total="total" :items-per-page="pageSize" :disabled="loading || busy" @update:page="load" />
    </div>
    <ResourceFormModal v-model:open="formOpen" :resource="editTarget" @saved="onSaved" />
    <ReviewHistoryModal v-model:open="historyOpen" :resource="target" />
    <ResourceArchiveModal v-model:open="archiveOpen" :resource="target" @archived="load()" @refresh="load()" />
    <ResourceDetailModal v-model:open="detailOpen" :resource-id="target?.id ?? null" />
    <UModal v-model:open="withdrawOpen" title="撤回投稿" :dismissible="!busy"
      :description="target?.status === 'approved' ? '撤回后，资源将从公开目录下架并恢复为草稿。' : '撤回后，资源将退出审核队列并恢复为草稿。'">
      <template #footer>
        <UButton color="neutral" variant="outline" :disabled="busy" @click="withdrawOpen = false">取消</UButton>
        <UButton color="warning" :loading="busy" @click="target && changeStatus(target, 'withdraw')">确认撤回</UButton>
      </template>
    </UModal>
  </StudentLayout>
</template>

<style scoped>
.submissions-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 10px; }
.submissions-count { margin: 0 0 12px; color: var(--lh-text-secondary); font-size: 13px; font-variant-numeric: tabular-nums; }
.submissions-count strong { color: var(--lh-primary); font-weight: 600; }
.submissions-list { display: grid; gap: 10px; margin: 0; padding: 0; list-style: none; }
.submission { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; padding: 16px; border: 1px solid var(--lh-border); border-radius: 12px; background: var(--lh-surface); }
.submission__info { display: grid; gap: 6px; flex: 1 1 240px; min-width: 0; }
.submission__title, .submission__actions { display: flex; align-items: center; gap: 8px; min-width: 0; }
.submission__actions { flex-wrap: wrap; }
@media (max-width: 639px) { .submission__info { flex-basis: 100%; } }
</style>
