<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import AsyncRegion from '../components/common/AsyncRegion.vue'
import BaseCard from '../components/common/BaseCard.vue'
import StatCard from '../components/common/StatCard.vue'
import { ApiError } from '../api/client'
import { listCourses } from '../api/courses'
import { listOperationLogs, type OperationLog } from '../api/operationLogs'
import { listAdminResources } from '../api/resources'
import { clearSession, useSession } from '../api/session'
import { listUsers } from '../api/users'
import { ACTION_COLORS, ACTION_LABELS, targetLabel } from '../constants/operationLog'

/*
 * 管理员首页概览。
 *
 * 统计口径（与后端接口一致，页面上如实标注）：
 * - 待审核资源：GET /resources/admin?status=pending 的 total —— 全部课程的待审资源
 * - 资源总数：GET /resources/admin 的 total —— 含草稿/待审/驳回/归档，含停用课程下的资源
 * - 课程总数：GET /courses 的 total —— 管理员可见全部课程（含停用）
 * - 用户总数：GET /users 的 total —— 含停用账户
 * 这些数字只取分页响应的 total，不额外拉列表，避免为了一个计数取回整页数据。
 *
 * 没有统计接口的指标（访问量、类型分布、审核时效）不在页面上展示，也不造估算值。
 */

const { currentUser } = useSession()
const isAdmin = computed(() => currentUser.value?.role === 'admin')

type StatState = 'loading' | 'ready' | 'error'
interface StatSlot {
  state: StatState
  value?: number
}

const pending = reactive<StatSlot>({ state: 'loading' })
const resources = reactive<StatSlot>({ state: 'loading' })
const courses = reactive<StatSlot>({ state: 'loading' })
const users = reactive<StatSlot>({ state: 'loading' })

const numberFormat = new Intl.NumberFormat('zh-CN')

async function loadCount(slot: StatSlot, fetcher: () => Promise<number>): Promise<void> {
  slot.state = 'loading'
  try {
    slot.value = await fetcher()
    slot.state = 'ready'
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 401) {
      clearSession()
      return
    }
    slot.value = undefined
    slot.state = 'error'
  }
}

function loadPending(): Promise<void> {
  return loadCount(pending, async () => (
    await listAdminResources({ status: 'pending', page: 1, page_size: 1 })
  ).total)
}

function loadResources(): Promise<void> {
  return loadCount(resources, async () => (await listAdminResources({ page: 1, page_size: 1 })).total)
}

function loadCourses(): Promise<void> {
  return loadCount(courses, async () => (await listCourses({ page: 1, page_size: 1 })).total)
}

function loadUsers(): Promise<void> {
  return loadCount(users, async () => (await listUsers({ page: 1, page_size: 1 })).total)
}

const pendingDisplay = computed(() => (
  pending.state === 'ready' && pending.value !== undefined
    ? numberFormat.format(pending.value)
    : '—'
))

/* 最近操作日志：首页只取最新若干条，完整列表在 /admin/operation-logs */
const LOG_PREVIEW_SIZE = 8
const logs = ref<OperationLog[]>([])
const logsState = ref<'loading' | 'ready' | 'empty' | 'error'>('loading')
const logsRequestId = ref('')

async function loadLogs(): Promise<void> {
  logsState.value = 'loading'
  logsRequestId.value = ''
  try {
    const page = await listOperationLogs(1, {}, LOG_PREVIEW_SIZE)
    logs.value = page.items
    logsState.value = page.items.length ? 'ready' : 'empty'
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 401) {
      clearSession()
      return
    }
    logs.value = []
    logsRequestId.value = cause instanceof ApiError ? cause.requestId : ''
    logsState.value = 'error'
  }
}

const logColumns = [
  { accessorKey: 'created_at', header: '时间', meta: { class: { th: 'w-[128px]', td: 'whitespace-nowrap text-muted' } } },
  { accessorKey: 'actor_id', header: '操作人', meta: { class: { th: 'w-[84px]', td: 'whitespace-nowrap text-muted' } } },
  { accessorKey: 'action', header: '操作', meta: { class: { th: 'w-[120px]' } } },
  { accessorKey: 'target_type', header: '对象', meta: { class: { th: 'w-[110px]', td: 'whitespace-nowrap text-muted' } } },
  // 摘要吃掉剩余宽度
  { accessorKey: 'summary', header: '摘要', meta: { class: { th: '' } } },
]

const logTime = new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
})

onMounted(() => {
  if (!isAdmin.value) return
  void loadPending()
  void loadResources()
  void loadCourses()
  void loadUsers()
  void loadLogs()
})
</script>

<template>
  <AdminLayout>
    <UAlert
      v-if="!isAdmin"
      color="warning"
      variant="soft"
      title="仅管理员可查看首页概览。"
      description="请使用管理员账号登录。"
    />

    <template v-else>
      <div class="overview-stats">
        <!-- 待审核优先：主行动指标，点击进入审核队列 -->
        <UCard :ui="{ body: 'p-5 sm:p-5' }">
          <div class="pending">
            <div class="pending__head">
              <p class="pending__label">待审核资源</p>
              <UIcon name="i-lucide-inbox" class="pending__icon" aria-hidden="true" />
            </div>
            <p class="pending__value" :class="{ 'pending__value--empty': pending.state !== 'ready' }">
              {{ pendingDisplay }}
            </p>
            <p v-if="pending.state === 'error'" class="pending__hint">
              加载失败
              <UButton size="xs" variant="link" color="primary" class="pending__retry" @click="loadPending">
                重试
              </UButton>
            </p>
            <RouterLink v-else to="/admin/reviews" class="pending__link">
              去审核
              <UIcon name="i-lucide-arrow-right" aria-hidden="true" />
            </RouterLink>
          </div>
        </UCard>

        <StatCard
          label="资源总数"
          icon="i-lucide-library"
          :value="resources.value"
          :state="resources.state"
          hint="全部状态，含停用课程下的资源"
          @retry="loadResources"
        />
        <StatCard
          label="课程总数"
          icon="i-lucide-book-open"
          :value="courses.value"
          :state="courses.state"
          hint="含已停用课程"
          @retry="loadCourses"
        />
        <StatCard
          label="用户总数"
          icon="i-lucide-users"
          :value="users.value"
          :state="users.state"
          hint="含已停用账户"
          @retry="loadUsers"
        />
      </div>

      <div class="overview-logs">
        <BaseCard density="compact">
          <template #title>
            <h2>最近操作日志</h2>
          </template>
          <template #action>
            <UButton to="/admin/operation-logs" size="xs" variant="ghost" trailing-icon="i-lucide-arrow-right">
              查看全部
            </UButton>
          </template>

          <AsyncRegion
            :status="logsState"
            :request-id="logsRequestId"
            :skeleton-rows="4"
            empty-title="还没有操作记录"
            empty-description="审核、归档、用户变更等操作会记录在这里。"
            empty-icon="i-lucide-scroll-text"
            error-title="操作日志加载失败"
            @retry="loadLogs"
          >
            <UTable class="overview-log-table" :data="logs" :columns="logColumns"
              :ui="{ base: 'w-full table-fixed', td: 'py-2' }">
              <template #created_at-cell="{ row }">
                {{ logTime.format(new Date(row.original.created_at)) }}
              </template>
              <template #actor_id-cell="{ row }">#{{ row.original.actor_id }}</template>
              <template #action-cell="{ row }">
                <UBadge :color="ACTION_COLORS[row.original.action] ?? 'neutral'" variant="subtle" size="sm">
                  {{ ACTION_LABELS[row.original.action] ?? row.original.action }}
                </UBadge>
              </template>
              <template #target_type-cell="{ row }">
                {{ targetLabel(row.original.target_type) }} #{{ row.original.target_id }}
              </template>
              <template #summary-cell="{ row }">
                <span class="log-summary" :title="row.original.summary">{{ row.original.summary || '—' }}</span>
              </template>
            </UTable>
          </AsyncRegion>
        </BaseCard>
      </div>
    </template>
  </AdminLayout>
</template>

<style scoped>
.overview-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.overview-logs {
  margin-top: 16px;
}

/* 待审核卡：与指标卡同尺寸，但多一行行动入口 */
.pending {
  display: grid;
  gap: 8px;
}

.pending__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.pending__label {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 14px;
}

.pending__icon {
  width: 20px;
  height: 20px;
  color: var(--lh-primary);
}

.pending__value {
  margin: 0;
  color: var(--lh-text);
  font-size: 32px;
  font-weight: 700;
  line-height: 40px;
  font-variant-numeric: tabular-nums;
}

.pending__value--empty {
  color: var(--lh-text-dimmed);
}

.pending__hint {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.pending__retry {
  padding: 0;
  vertical-align: baseline;
}

.pending__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  justify-self: start;
  color: var(--lh-primary);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.pending__link:hover {
  text-decoration: underline;
}

.log-summary {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 表格宽度不依赖 ui.base 里的 w-full，同时覆盖容器和 table 元素 */
.overview-log-table,
.overview-log-table :deep(table) {
  width: 100%;
}

@media (max-width: 1023px) {
  .overview-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
