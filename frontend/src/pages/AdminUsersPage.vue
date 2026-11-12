<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { useSession } from '../api/session'
import { listUsers, updateUser } from '../api/users'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import type { User, UserRole, UserUpdatePayload } from '../types/user'

/*
 * 管理员用户管理：分页列表 + 行内改角色 / 启停。
 * 规则全部以后端为准：改自己会返回 409 ADMIN_SELF_CHANGE_FORBIDDEN，
 * 有课程的教师降级会返回 409 COURSE_TRANSFER_REQUIRED，前端只负责如实展示。
 */
const PAGE_SIZE = 20

const { currentUser } = useSession()

const users = ref<User[]>([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const roleFilter = ref<'all' | UserRole>('all')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

const status = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')
const actionError = ref('')
const pendingId = ref<number | null>(null)

const ROLE_FILTERS: { value: 'all' | UserRole; label: string }[] = [
  { value: 'all', label: '全部角色' },
  { value: 'student', label: '学生' },
  { value: 'teacher', label: '教师' },
  { value: 'admin', label: '管理员' },
]

const STATUS_FILTERS: { value: 'all' | 'active' | 'inactive'; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '已启用' },
  { value: 'inactive', label: '已停用' },
]

const ROLE_ITEMS: { value: UserRole; label: string }[] = [
  { value: 'student', label: '学生' },
  { value: 'teacher', label: '教师' },
  { value: 'admin', label: '管理员' },
]

/** 四列表格统一用 40/20/20/20：主内容列不独吞宽度，其余列平均铺开 */
const columns = [
  { accessorKey: 'display_name', header: '用户', meta: { class: { th: 'w-[40%]' } } },
  {
    accessorKey: 'role',
    header: '角色',
    meta: { class: { th: 'w-[20%]' } },
  },
  {
    accessorKey: 'is_active',
    header: '状态',
    meta: { class: { th: 'w-[20%]' } },
  },
  {
    accessorKey: 'created_at',
    header: '注册时间',
    meta: { class: { th: 'w-[20%]' } },
  },
]

const isSelf = (user: User): boolean => currentUser.value?.id === user.id

/** 角色 → 中文，只读单元格和下拉共用同一份文案 */
function roleLabel(role: UserRole): string {
  return ROLE_ITEMS.find((item) => item.value === role)?.label ?? role
}

function initialOf(user: User): string {
  const first = Array.from(user.display_name.trim())[0] ?? ''
  return first ? first.toUpperCase() : '?'
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(date)
}

async function load(): Promise<void> {
  status.value = 'loading'
  actionError.value = ''

  try {
    const data = await listUsers({
      page: page.value,
      page_size: PAGE_SIZE,
      role: roleFilter.value === 'all' ? null : roleFilter.value,
      is_active: statusFilter.value === 'all' ? null : statusFilter.value === 'active',
      q: keyword.value.trim() || undefined,
    })
    users.value = data.items
    total.value = data.total
    status.value = 'ready'
  } catch (e) {
    loadError.value = e instanceof ApiError ? e.message : '加载失败，请稍后重试。'
    status.value = 'error'
  }
}

async function mutate(id: number, payload: UserUpdatePayload): Promise<void> {
  actionError.value = ''
  pendingId.value = id
  try {
    const updated = await updateUser(id, payload)
    users.value = users.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (e) {
    actionError.value = e instanceof ApiError ? e.message : '操作失败，请稍后重试。'
  } finally {
    pendingId.value = null
  }
}

function onRoleChange(user: User, value: unknown): void {
  if (value === user.role) return
  if (value !== 'student' && value !== 'teacher' && value !== 'admin') return
  void mutate(user.id, { role: value })
}

function onToggleActive(user: User): void {
  void mutate(user.id, { is_active: !user.is_active })
}

function onPageChange(next: number): void {
  page.value = next
  void load()
}

function resetAndLoad(): void {
  page.value = 1
  void load()
}

let keywordTimer: number | undefined

watch(keyword, () => {
  window.clearTimeout(keywordTimer)
  keywordTimer = window.setTimeout(resetAndLoad, 300)
})

watch([roleFilter, statusFilter], resetAndLoad)

onMounted(() => void load())
onBeforeUnmount(() => window.clearTimeout(keywordTimer))
</script>

<template>
  <AdminLayout>
    <div class="filters page-toolbar">
      <UInput
        v-model="keyword"
        icon="i-lucide-search"
        size="lg"
        placeholder="搜索用户名"
        aria-label="搜索用户名"
        class="filters__search"
      />
      <USelect
        v-model="roleFilter"
        :items="ROLE_FILTERS"
        size="lg"
        aria-label="按角色筛选"
        class="filters__select"
      />
      <USelect
        v-model="statusFilter"
        :items="STATUS_FILTERS"
        size="lg"
        aria-label="按状态筛选"
        class="filters__select"
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
        :data="users"
        :columns="columns"
        :loading="status === 'loading'"
        caption="用户列表"
        empty="没有符合条件的用户，换个筛选条件试试。"
        :ui="{
          base: 'min-w-full table-fixed table-center',
          th: 'h-10 px-3 py-0 text-xs',
          td: 'h-14 px-3 py-0 text-sm text-default',
          tr: 'hover:bg-elevated/50',
        }"
      >
        <template #display_name-cell="{ row }">
          <div class="user-cell">
            <span class="user-cell__avatar" aria-hidden="true">{{ initialOf(row.original) }}</span>
            <div class="user-cell__text">
              <p class="user-cell__name">
                {{ row.original.display_name }}
                <span v-if="isSelf(row.original)" class="user-cell__self">（我）</span>
              </p>
              <p class="user-cell__username">@{{ row.original.username }}</p>
            </div>
          </div>
        </template>

        <template #role-cell="{ row }">
          <!-- 自己的账号不能改，所以不给控件：只读文本 + 锁图标，避免"灰掉但仍像能点" -->
          <span v-if="isSelf(row.original)" class="locked-cell" title="不能修改自己的角色">
            <UIcon name="i-lucide-lock" class="locked-cell__icon" aria-hidden="true" />
            {{ roleLabel(row.original.role) }}
          </span>
          <USelect
            v-else
            :model-value="row.original.role"
            :items="ROLE_ITEMS"
            size="sm"
            class="role-select"
            :disabled="pendingId === row.original.id"
            :aria-label="`${row.original.display_name} 的角色`"
            @update:model-value="(value) => onRoleChange(row.original, value)"
          />
        </template>

        <template #is_active-cell="{ row }">
          <span v-if="isSelf(row.original)" class="locked-cell" title="不能停用自己的账号">
            <UIcon name="i-lucide-lock" class="locked-cell__icon" aria-hidden="true" />
            {{ row.original.is_active ? '启用' : '停用' }}
          </span>
          <div v-else class="status-cell">
            <USwitch
              :model-value="row.original.is_active"
              :disabled="pendingId === row.original.id"
              :aria-label="`${row.original.display_name} 的账户状态`"
              @update:model-value="onToggleActive(row.original)"
            />
            <span class="status-cell__label">
              {{ row.original.is_active ? '启用' : '停用' }}
            </span>
          </div>
        </template>

        <template #created_at-cell="{ row }">
          <span class="date-cell">{{ formatDate(row.original.created_at) }}</span>
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
      <p class="table-footer__total">共 <span class="table-footer__count">{{ total }}</span> 人</p>
      <!-- 只有超过一页才需要分页器，一页时那排按钮只是噪音 -->
      <UPagination
        v-if="total > PAGE_SIZE"
        :page="page"
        :total="total"
        :items-per-page="PAGE_SIZE"
        size="sm"
        @update:page="onPageChange"
      />
    </div>
  </AdminLayout>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.filters__search {
  width: min(100%, 260px);
}

.filters__select {
  width: 150px;
}

.action-error {
  margin-bottom: 16px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.user-cell__avatar {
  display: grid;
  flex: none;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
  font-size: 14px;
  font-weight: 600;
}

.user-cell__text {
  min-width: 0;
}

.user-cell__name {
  margin: 0;
  overflow: hidden;
  color: var(--lh-text);
  font-size: 14px;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.user-cell__self {
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.user-cell__username {
  margin: 0;
  overflow: hidden;
  color: var(--lh-text-secondary);
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.role-select {
  width: 108px;
}

.status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* 自己的账号：只读单元格，锁图标表明"不能改" */
.locked-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--lh-text-secondary);
  font-size: 13px;
  white-space: nowrap;
}

.locked-cell__icon {
  flex: none;
  width: 14px;
  height: 14px;
  color: var(--lh-control-border);
}

.status-cell__label {
  color: var(--lh-text-secondary);
  font-size: 13px;
}

.date-cell {
  color: var(--lh-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
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

/* 数字用主题色突出，其余文字保持次要色 */
.table-footer__count {
  color: var(--lh-primary);
  font-weight: 600;
}

@media (max-width: 767px) {
  .filters__search,
  .filters__select {
    width: 100%;
  }
}
</style>
