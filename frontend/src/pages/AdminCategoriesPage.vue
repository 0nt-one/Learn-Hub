<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { createCategory, listCategories, updateCategory } from '../api/categories'
import { ApiError } from '../api/client'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import type { Category } from '../types/category'

/*
 * 管理员分类管理：列表（UTable）+ 新建 / 编辑（弹窗）+ 行内启停。 * 分类是单层结构，名称唯一；重名由后端返回 409 CATEGORY_NAME_EXISTS，这里原样展示。 */
const PAGE_SIZE = 20

const items = ref<Category[]>([])
const total = ref(0)
const page = ref(1)
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

const status = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')
const actionError = ref('')
const pendingId = ref<number | null>(null)

const formOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ name: '', description: '' })

const isEditing = computed(() => editingId.value !== null)

const STATUS_FILTERS: { value: 'all' | 'active' | 'inactive'; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '已启用' },
  { value: 'inactive', label: '已停用' },
]

/**
 * 列定义。自定义单元格通过 #<id>-cell 插槽渲染， * 宽度约束写在 meta.class 里，交给表格主题合并。 */
// 四列表格统一用 40/20/20/20：主内容列不独吞宽度，其余列平均铺开
const columns = [
  { accessorKey: 'name', header: '分类', meta: { class: { th: 'w-[40%]' } } },
  {
    accessorKey: 'is_active',
    header: '状态',
    meta: { class: { th: 'w-[20%]' } },
  },
  {
    accessorKey: 'updated_at',
    header: '更新时间',
    meta: { class: { th: 'w-[20%]' } },
  },
  {
    id: 'actions',
    header: '操作',
    meta: { class: { th: 'w-[20%]' } },
  },
]

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(date)
}

async function load(): Promise<void> {
  status.value = 'loading'
  actionError.value = ''

  try {
    const data = await listCategories({
      page: page.value,
      page_size: PAGE_SIZE,
      is_active: statusFilter.value === 'all' ? null : statusFilter.value === 'active',
    })
    items.value = data.items
    total.value = data.total
    status.value = 'ready'
  } catch (e) {
    loadError.value = e instanceof ApiError ? e.message : '加载失败，请稍后重试。'
    status.value = 'error'
  }
}

async function toggleActive(category: Category): Promise<void> {
  actionError.value = ''
  pendingId.value = category.id
  try {
    const updated = await updateCategory(category.id, { is_active: !category.is_active })
    items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (e) {
    actionError.value = e instanceof ApiError ? e.message : '操作失败，请稍后重试。'
  } finally {
    pendingId.value = null
  }
}

function openCreate(): void {
  editingId.value = null
  form.name = ''
  form.description = ''
  formError.value = ''
  formOpen.value = true
}

function openEdit(category: Category): void {
  editingId.value = category.id
  form.name = category.name
  form.description = category.description
  formError.value = ''
  formOpen.value = true
}

async function submit(): Promise<void> {
  const name = form.name.trim()
  const description = form.description.trim()

  if (name.length === 0) {
    formError.value = '请填写分类名称'
    return
  }
  if (name.length > 64) {
    formError.value = '分类名称最多 64 个字符'
    return
  }
  if (description.length > 1000) {
    formError.value = '描述最多 1000 个字符'
    return
  }

  saving.value = true
  formError.value = ''

  try {
    if (editingId.value !== null) {
      const updated = await updateCategory(editingId.value, { name, description })
      items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
    } else {
      await createCategory({ name, description })
      page.value = 1
      await load()
    }
    formOpen.value = false
  } catch (e) {
    formError.value = e instanceof ApiError ? e.message : '保存失败，请稍后重试。'
  } finally {
    saving.value = false
  }
}

function onPageChange(next: number): void {
  page.value = next
  void load()
}

watch(statusFilter, () => {
  page.value = 1
  void load()
})

onMounted(() => void load())
</script>

<template>
  <AdminLayout>
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
      <UButton class="toolbar__primary" color="primary" size="lg" icon="i-lucide-plus" @click="openCreate">
        新建分类
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
        caption="分类列表"
        empty="还没有分类，点右上角「新建分类」开始。"
        :ui="{
          base: 'min-w-full table-fixed table-center',
          th: 'h-10 px-3 py-0 text-xs',
          td: 'h-14 px-3 py-0 text-sm text-default',
          tr: 'hover:bg-elevated/50',
        }"
      >
        <template #name-cell="{ row }">
          <div class="category-cell">
            <span
              class="category-cell__dot"
              :class="{ 'category-cell__dot--off': !row.original.is_active }"
              aria-hidden="true"
            />
            <div class="category-cell__text">
              <p class="category-cell__name">{{ row.original.name }}</p>
              <p class="category-cell__desc">{{ row.original.description || '暂无描述' }}</p>
            </div>
          </div>
        </template>

        <template #is_active-cell="{ row }">
          <div class="status-cell">
            <USwitch
              :model-value="row.original.is_active"
              :disabled="pendingId === row.original.id"
              :aria-label="`${row.original.name} 的启用状态`"
              @update:model-value="toggleActive(row.original)"
            />
            <span class="status-cell__label">
              {{ row.original.is_active ? '启用' : '停用' }}
            </span>
          </div>
        </template>

        <template #updated_at-cell="{ row }">
          <span class="date-cell">{{ formatDate(row.original.updated_at) }}</span>
        </template>

        <template #actions-cell="{ row }">
          <UButton
            color="neutral"
            variant="ghost"
            size="sm"
            icon="i-lucide-pencil"
            @click="openEdit(row.original)"
          >
            编辑
          </UButton>
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
      <p class="table-footer__total">共 <span class="table-footer__count">{{ total }}</span> 个分类</p>
      <!-- 只有超过一页才需要分页器 -->
      <UPagination
        v-if="total > PAGE_SIZE"
        :page="page"
        :total="total"
        :items-per-page="PAGE_SIZE"
        size="sm"
        @update:page="onPageChange"
      />
    </div>

    <UModal v-model:open="formOpen" :title="isEditing ? '编辑分类' : '新建分类'">
      <template #body>
        <div class="form">
          <label class="form__field">
            <span class="form__label">名称 <span aria-hidden="true">*</span></span>
            <UInput v-model="form.name" maxlength="64" placeholder="例如：高等数学" class="w-full" />
          </label>

          <label class="form__field">
            <span class="form__label">描述</span>
            <UTextarea
              v-model="form.description"
              :rows="6"
              maxlength="1000"
              placeholder="这个分类适合放什么资源"
              class="w-full"
              :ui="{ base: 'min-h-[132px]' }"
            />
          </label>

          <p v-if="formError" class="form__error" role="alert">{{ formError }}</p>
        </div>
      </template>

      <template #footer>
        <div class="modal-footer">
          <UButton color="neutral" variant="ghost" :disabled="saving" @click="formOpen = false">
            取消
          </UButton>
          <UButton color="primary" :loading="saving" @click="submit">
            {{ isEditing ? '保存修改' : '创建分类' }}
          </UButton>
        </div>
      </template>
    </UModal>
  </AdminLayout>
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

/* 工具栏里的控件一律不收缩、不换行：否则中文标签会被挤成两行 */
.toolbar__filters > * {
  flex: none;
  white-space: nowrap;
}

/* 主操作固定在最右，靠 auto 外边距而不是 space-between，避免筛选组被压窄换行 */
.toolbar__primary {
  flex: none;
  margin-left: auto;
  white-space: nowrap;
}

.toolbar__select {
  width: 150px;
}

.action-error {
  margin-bottom: 16px;
}

.category-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.category-cell__dot {
  flex: none;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--lh-primary);
}

.category-cell__dot--off {
  background: var(--lh-control-border);
}

.category-cell__text {
  min-width: 0;
}

.category-cell__name {
  margin: 0;
  overflow: hidden;
  color: var(--lh-text);
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.category-cell__desc {
  margin: 0;
  overflow: hidden;
  max-width: 420px;
  color: var(--lh-text-secondary);
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
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

.form__error {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--lh-danger-soft);
  color: var(--lh-danger);
  font-size: 13px;
  line-height: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 767px) {
  .toolbar {
    flex-wrap: wrap;
  }

  .toolbar__filters {
    width: 100%;
  }

  .toolbar__select,
  .toolbar__primary {
    width: 100%;
  }
}
</style>
