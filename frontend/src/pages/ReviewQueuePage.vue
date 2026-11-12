<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { createReview, listPendingReviews } from '../api/reviews'
import { useSession } from '../api/session'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import ResourceTypeBadge from '../components/resources/ResourceTypeBadge.vue'
import ReviewHistoryModal from '../components/resources/ReviewHistoryModal.vue'
import ResourceArchiveModal from '../components/resources/ResourceArchiveModal.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import TeacherLayout from '../layouts/TeacherLayout.vue'
import type { Resource } from '../types/resource'
import type { ReviewDecision } from '../types/review'

/*
 * 待审队列：教师与管理员共用一页，外壳按角色切换。
 * 后端 GET /reviews/pending 已经按权限收敛：
 * - 教师：只看自己负责课程下的投稿
 * - 管理员：看全部
 * - 两边都排除自己的投稿（不能审自己）
 * 审核决定走 POST /resources/{id}/reviews，驳回必须填写意见。
 */
const PAGE_SIZE = 20

const { currentUser, accessToken } = useSession()
let loadSequence = 0
onUnmounted(() => { loadSequence++ })
watch(accessToken, () => { loadSequence++; items.value = []; total.value = 0 }, { flush: 'sync' })
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const layout = computed(() => (isAdmin.value ? AdminLayout : TeacherLayout))

const items = ref<Resource[]>([])
const total = ref(0)
const page = ref(1)

const status = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')
const actionError = ref('')

const modalOpen = ref(false)
const decision = ref<ReviewDecision>('approved')
const reviewing = ref<Resource | null>(null)
const historyResource = ref<Resource | null>(null)
const historyOpen = ref(false)
const archiveOpen = ref(false)
const archiveTarget = ref<Resource | null>(null)
function showArchive(resource: Resource) {
  if (!isAdmin.value) return
  archiveTarget.value = resource
  archiveOpen.value = true
}
function showHistory(resource: Resource) { historyResource.value = resource; historyOpen.value = true }
const comment = ref('')
const modalError = ref('')
const submitting = ref(false)

// 四列表格统一用 40/20/20/20：主内容列不独吞宽度，其余列平均铺开
const columns = computed(() => [
  { accessorKey: 'title', header: '资源', meta: { class: { th: 'w-[40%]' } } },
  { accessorKey: 'course_id', header: '归属', meta: { class: { th: 'w-[20%]' } } },
  {
    accessorKey: 'created_at',
    header: '提交时间',
    meta: { class: { th: 'w-[20%]' } },
  },
  {
    id: 'actions',
    header: '操作',
    meta: { class: { th: 'w-[20%]' } },
  },
])

const modalTitle = computed(() => (decision.value === 'approved' ? '通过资源' : '驳回资源'))
const confirmLabel = computed(() => (decision.value === 'approved' ? '确认通过' : '确认驳回'))

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(date)
}

async function load(): Promise<void> {
  const seq = ++loadSequence
  status.value = 'loading'
  actionError.value = ''

  try {
    const data = await listPendingReviews({ page: page.value, page_size: PAGE_SIZE })
    if (seq !== loadSequence) return
    const lastPage = Math.max(1, Math.ceil(data.total / PAGE_SIZE))
    if (page.value > lastPage) { page.value = lastPage; await load(); return }
    items.value = data.items
    total.value = data.total
    status.value = 'ready'
  } catch (e) {
    if (seq !== loadSequence) return
    loadError.value = e instanceof ApiError ? e.message : '加载失败，请稍后重试。'
    status.value = 'error'
  }
}

function openDecision(resource: Resource, next: ReviewDecision): void {
  reviewing.value = resource
  decision.value = next
  comment.value = ''
  modalError.value = ''
  modalOpen.value = true
}

async function confirmDecision(): Promise<void> {
  const resource = reviewing.value
  if (!resource) return

  const text = comment.value.trim()
  if (decision.value === 'rejected' && !text) {
    modalError.value = '驳回必须填写审核意见，作者需要知道要改什么。'
    return
  }

  submitting.value = true
  modalError.value = ''

  try {
    await createReview(resource.id, {
      expected_version: resource.version_id,
      decision: decision.value,
      comment: text,
    })

    modalOpen.value = false
    // 审完就不再是待审，直接从队列里去掉，不用整表刷新
    items.value = items.value.filter((item) => item.id !== resource.id)
    total.value = Math.max(0, total.value - 1)

    // 当前页被审空且还有上一页时退回上一页
    if (items.value.length === 0 && page.value > 1) {
      page.value -= 1
      void load()
    }
  } catch (e) {
    if (e instanceof ApiError) {
      if (e.code === 'SELF_REVIEW_FORBIDDEN') {
        modalError.value = '不能审核自己提交的资源。'
      } else if (e.code === 'INVALID_STATE') {
        modalError.value = '这条资源已经不在待审状态（可能刚被其他人处理）。'
      } else if (e.code === 'VERSION_CONFLICT') {
        modalError.value = '资源在你看的这段时间被修改过，请关闭弹窗刷新后重试。'
      } else {
        modalError.value = e.message
      }
    } else {
      modalError.value = '提交审核决定失败，请稍后重试。'
    }
  } finally {
    submitting.value = false
  }
}

function onPageChange(next: number): void {
  page.value = next
  void load()
}

onMounted(() => void load())
</script>

<template>
  <component :is="layout">
    <div class="toolbar page-toolbar">
      <div class="toolbar__filters">
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
        caption="待审资源"
        empty="队列已经清空了，暂时没有待审资源。"
        :ui="{
          base: 'w-full min-w-[800px] table-fixed table-center',
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
          <p class="owner-cell">{{ row.original.course_title }}</p>
          <p class="owner-cell__sub">{{ row.original.category_name }}</p>
        </template>

        <template #created_at-cell="{ row }">
          <span class="date-cell">{{ formatDate(row.original.created_at) }}</span>
        </template>

        <template #actions-cell="{ row }">
          <div class="actions">
            <UButton v-if="isAdmin" color="error" variant="ghost" size="sm" icon="i-lucide-archive" @click="showArchive(row.original)">归档</UButton>
            <UButton color="neutral" variant="ghost" size="sm" icon="i-lucide-history" @click="showHistory(row.original)">审核历史</UButton>
            <UButton
              :to="row.original.url"
              target="_blank"
              rel="noopener noreferrer"
              color="neutral"
              variant="ghost"
              size="sm"
              icon="i-lucide-external-link"
            >
              查看
            </UButton>
            <UButton
              color="success"
              variant="soft"
              size="sm"
              icon="i-lucide-circle-check"
              @click="openDecision(row.original, 'approved')"
            >
              通过
            </UButton>
            <UButton
              color="error"
              variant="soft"
              size="sm"
              icon="i-lucide-circle-x"
              @click="openDecision(row.original, 'rejected')"
            >
              驳回
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
      <p class="table-footer__total">共 <span class="table-footer__count">{{ total }}</span> 条待审</p>
      <UPagination
        v-if="total > PAGE_SIZE"
        :page="page"
        :total="total"
        :items-per-page="PAGE_SIZE"
        size="sm"
        @update:page="onPageChange"
      />
    </div>

    <UModal
      v-model:open="modalOpen"
      :title="modalTitle"
      :description="reviewing?.title"
    >
      <template #body>
        <div class="form">
          <div class="form__field">
            <label class="form__label" for="review-comment">
              审核意见
              <span v-if="decision === 'rejected'" class="form__required" aria-hidden="true">*</span>
            </label>
            <UTextarea
              id="review-comment"
              v-model="comment"
              :rows="5"
              maxlength="2000"
              :placeholder="decision === 'rejected' ? '说明哪里需要修改，作者会看到这段意见' : '可选，例如：内容完整，已通过'"
              class="w-full"
            />
            <p v-if="modalError" class="form__error-text">{{ modalError }}</p>
          </div>
        </div>
      </template>

      <template #footer>
        <div class="modal-footer">
          <UButton color="neutral" variant="ghost" :disabled="submitting" @click="modalOpen = false">
            取消
          </UButton>
          <UButton
            :color="decision === 'approved' ? 'success' : 'error'"
            :loading="submitting"
            @click="confirmDecision"
          >
            {{ confirmLabel }}
          </UButton>
        </div>
      </template>
    </UModal>
    <ReviewHistoryModal v-model:open="historyOpen" :resource="historyResource" />
    <ResourceArchiveModal v-model:open="archiveOpen" :resource="archiveTarget" @archived="load" @refresh="load" />
  </component>
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

.action-error {
  margin-bottom: 16px;
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
  margin: 0;
  color: var(--lh-text);
  font-size: 13px;
  line-height: 20px;
}

.owner-cell__sub {
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

.form {
  display: grid;
  gap: 16px;
}

.form__field {
  display: grid;
  gap: 6px;
}

.form__label {
  color: var(--lh-text);
  font-size: 14px;
  font-weight: 600;
}

.form__required {
  color: var(--lh-danger);
}

.form__error-text {
  margin: 0;
  color: var(--lh-danger);
  font-size: 12px;
  line-height: 18px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
