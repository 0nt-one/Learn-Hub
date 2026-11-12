<script setup lang="ts">
import { onMounted, ref } from 'vue'
import TeacherLayout from '../layouts/TeacherLayout.vue'
import AsyncRegion from '../components/common/AsyncRegion.vue'
import BaseCard from '../components/common/BaseCard.vue'
import StatusBadge from '../components/resources/StatusBadge.vue'
import { ApiError } from '../api/client'
import { listMyCourses } from '../api/courses'
import { listMyResources } from '../api/resources'
import { listPendingReviews } from '../api/reviews'
import { clearSession } from '../api/session'
import type { Resource } from '../types/resource'

/*
 * 教师工作台：优先回答"今天该处理什么"。
 *
 * 两个列表刻意分开，语义不同，不能混：
 * - 待我审核：GET /reviews/pending —— 别人提交到"我负责的课程"下的资源，按提交时间升序（先到先审）
 * - 我的投稿：GET /resources/mine —— 我自己创建的资源及其审核状态，按创建时间倒序
 * 课程概览只用 GET /courses/mine，这是教师端唯一能拿到"我负责的课程"的接口。
 *
 * 没有聚合接口，都是分页接口取少量数据、总数取 total。
 */

const PENDING_PREVIEW_SIZE = 5
const MY_RESOURCE_PREVIEW_SIZE = 6

const pendingItems = ref<Resource[]>([])
const pendingTotal = ref(0)
const pendingState = ref<'loading' | 'ready' | 'empty' | 'error'>('loading')
const pendingRequestId = ref('')

const myResources = ref<Resource[]>([])
const resourcesTotal = ref(0)
const resourcesState = ref<'loading' | 'ready' | 'empty' | 'error'>('loading')
const resourcesRequestId = ref('')

const courseTotal = ref<number | undefined>(undefined)
const courseState = ref<'loading' | 'ready' | 'error'>('loading')

const whenFormat = new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
})

function formatWhen(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '时间未知' : whenFormat.format(date)
}

function handleFailure(cause: unknown): string {
  if (cause instanceof ApiError && cause.status === 401) {
    clearSession()
    return ''
  }
  return cause instanceof ApiError ? cause.requestId : ''
}

async function loadPending(): Promise<void> {
  pendingState.value = 'loading'
  pendingRequestId.value = ''
  try {
    const page = await listPendingReviews({ page: 1, page_size: PENDING_PREVIEW_SIZE })
    pendingItems.value = page.items
    pendingTotal.value = page.total
    pendingState.value = page.items.length ? 'ready' : 'empty'
  } catch (cause) {
    pendingItems.value = []
    pendingTotal.value = 0
    pendingRequestId.value = handleFailure(cause)
    pendingState.value = 'error'
  }
}

async function loadMyResources(): Promise<void> {
  resourcesState.value = 'loading'
  resourcesRequestId.value = ''
  try {
    const page = await listMyResources({ page: 1, page_size: MY_RESOURCE_PREVIEW_SIZE })
    myResources.value = page.items
    resourcesTotal.value = page.total
    resourcesState.value = page.items.length ? 'ready' : 'empty'
  } catch (cause) {
    myResources.value = []
    resourcesTotal.value = 0
    resourcesRequestId.value = handleFailure(cause)
    resourcesState.value = 'error'
  }
}

async function loadCourses(): Promise<void> {
  courseState.value = 'loading'
  try {
    const page = await listMyCourses({ page: 1, page_size: 1 })
    courseTotal.value = page.total
    courseState.value = 'ready'
  } catch (cause) {
    courseTotal.value = undefined
    handleFailure(cause)
    courseState.value = 'error'
  }
}

/* 待审队列沿用 /reviews/pending 的升序（先提交的先审），这里不重新排序 */
const resourceColumns = [
  { accessorKey: 'title', header: '资源' },
  { accessorKey: 'course_title', header: '课程', meta: { class: { th: 'w-[180px]', td: 'text-muted' } } },
  { accessorKey: 'status', header: '状态', meta: { class: { th: 'w-[120px]' } } },
  { accessorKey: 'updated_at', header: '更新时间', meta: { class: { th: 'w-[150px]', td: 'whitespace-nowrap text-muted' } } },
]

onMounted(() => {
  void loadPending()
  void loadMyResources()
  void loadCourses()
})
</script>

<template>
  <TeacherLayout>
    <div class="workbench-top">
      <BaseCard density="compact">
        <template #title>
          <h2>待我审核</h2>
        </template>
        <template #action>
          <UButton to="/teacher/reviews" size="xs" variant="ghost" trailing-icon="i-lucide-arrow-right">
            去审核
          </UButton>
        </template>

        <p v-if="pendingState === 'ready'" class="workbench-count">
          共 <strong>{{ pendingTotal }}</strong> 条待审，按提交时间先到先审
        </p>

        <AsyncRegion
          :status="pendingState"
          :request-id="pendingRequestId"
          :skeleton-rows="4"
          empty-title="没有待审资源"
          empty-description="别的老师和你自己投稿的资源进入待审后会出现在这里。"
          empty-icon="i-lucide-inbox"
          error-title="待审队列加载失败"
          @retry="loadPending"
        >
          <ul class="pending-list">
            <li v-for="item in pendingItems" :key="item.id" class="pending-item">
              <p class="pending-item__title">{{ item.title }}</p>
              <p class="pending-item__meta">
                <span>{{ item.course_title }}</span>
                <span aria-hidden="true">·</span>
                <span>投稿人 {{ item.owner_display_name }}</span>
                <span aria-hidden="true">·</span>
                <span>{{ formatWhen(item.created_at) }} 提交</span>
              </p>
            </li>
          </ul>
          <p v-if="pendingTotal > pendingItems.length" class="workbench-more">
            还有 {{ pendingTotal - pendingItems.length }} 条待审，进入队列查看。
          </p>
        </AsyncRegion>
      </BaseCard>

      <BaseCard density="compact">
        <template #title>
          <h2>我的课程</h2>
        </template>
        <template #action>
          <UButton to="/teacher/courses" size="xs" variant="ghost" trailing-icon="i-lucide-arrow-right">
            进入
          </UButton>
        </template>

        <div class="course-stat">
          <p class="course-stat__value" :class="{ 'course-stat__value--empty': courseState !== 'ready' }">
            {{ courseState === 'ready' && courseTotal !== undefined ? courseTotal : '—' }}
          </p>
          <p class="course-stat__hint">
            <template v-if="courseState === 'loading'">正在获取数据</template>
            <template v-else-if="courseState === 'error'">
              加载失败
              <UButton size="xs" variant="link" color="primary" class="course-stat__retry" @click="loadCourses">
                重试
              </UButton>
            </template>
            <template v-else>门课程由你负责，含已停用课程</template>
          </p>
        </div>
      </BaseCard>
    </div>

    <div class="workbench-bottom">
      <BaseCard density="compact">
        <template #title>
          <h2>我的资源</h2>
        </template>
        <template #action>
          <UButton to="/teacher/resources" size="xs" variant="ghost" trailing-icon="i-lucide-arrow-right">
            查看全部
          </UButton>
        </template>

        <p v-if="resourcesState === 'ready'" class="workbench-count">
          共 <strong>{{ resourcesTotal }}</strong> 份资源，最近提交在前
        </p>

        <AsyncRegion
          :status="resourcesState"
          :request-id="resourcesRequestId"
          :skeleton-rows="4"
          empty-title="还没有投稿"
          empty-description="在「我的资源」页右上角点「共享新资源」开始投稿。"
          empty-icon="i-lucide-folder-open"
          error-title="我的资源加载失败"
          @retry="loadMyResources"
        >
          <UTable class="my-resource-table" :data="myResources" :columns="resourceColumns"
            :ui="{ base: 'w-full table-fixed', td: 'py-2' }">
            <template #title-cell="{ row }">
              <span class="resource-title" :title="row.original.title">{{ row.original.title }}</span>
            </template>
            <template #status-cell="{ row }">
              <StatusBadge :status="row.original.status" />
            </template>
            <template #updated_at-cell="{ row }">{{ formatWhen(row.original.updated_at) }}</template>
          </UTable>

          <!--
            只有 draft / rejected 能在「我的资源」页修改，且编辑弹窗是该页的内部状态，
            没有可深链的地址，所以这里只提供进入列表的入口，不做「去修改」直达按钮。
          -->
          <p class="workbench-note">
            待审核的资源不能修改；草稿和被驳回的资源可在「我的资源」里继续编辑。
          </p>
        </AsyncRegion>
      </BaseCard>
    </div>
  </TeacherLayout>
</template>

<style scoped>
.workbench-top {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 16px;
}

.workbench-bottom {
  margin-top: 16px;
}

.workbench-count {
  margin: 0 0 12px;
  color: var(--lh-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.workbench-count strong {
  color: var(--lh-primary);
  font-weight: 600;
}

.workbench-more {
  margin: 12px 0 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.workbench-note {
  margin: 12px 0 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.pending-list {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}

.pending-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--lh-border);
}

.pending-item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.pending-item:first-child {
  padding-top: 0;
}

.pending-item__title {
  overflow: hidden;
  margin: 0;
  color: var(--lh-text);
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.pending-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 4px 0 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.course-stat {
  display: grid;
  gap: 8px;
}

.course-stat__value {
  margin: 0;
  color: var(--lh-text);
  font-size: 32px;
  font-weight: 700;
  line-height: 40px;
  font-variant-numeric: tabular-nums;
}

.course-stat__value--empty {
  color: var(--lh-text-dimmed);
}

.course-stat__hint {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.course-stat__retry {
  padding: 0;
  vertical-align: baseline;
}

.resource-title {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* table-fixed 不管表格自身宽度，显式钉成 100% 才不会右侧留白 */
.my-resource-table,
.my-resource-table :deep(table) {
  width: 100%;
}

@media (max-width: 1023px) {
  .workbench-top {
    grid-template-columns: 1fr;
  }
}
</style>
