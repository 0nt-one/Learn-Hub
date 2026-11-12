<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { createCourse, listCourses, listMyCourses, updateCourse } from '../api/courses'
import { useSession } from '../api/session'
import { listUsers } from '../api/users'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import TeacherLayout from '../layouts/TeacherLayout.vue'
import type { Course, CourseUpdatePayload } from '../types/course'

/*
 * 课程管理：教师与管理员共用一页，外壳按角色切换。 * - 教师：查看自己负责的课程，包括停用课程 * - 管理员：可筛选启用/停用，可指定或转移负责人
 */
const PAGE_SIZE = 20
const CODE_PATTERN = /^[A-Z0-9-]+$/

const { currentUser } = useSession()
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const layout = computed(() => (isAdmin.value ? AdminLayout : TeacherLayout))

const items = ref<Course[]>([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

const status = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')
const actionError = ref('')
const pendingId = ref<number | null>(null)

const teacherOptions = ref<{ value: number; label: string }[]>([])

const formOpen = ref(false)
const editing = ref<Course | null>(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ code: '', title: '', description: '', teacherId: 0, isActive: true })

const isEditing = computed(() => editing.value !== null)

const STATUS_FILTERS: { value: 'all' | 'active' | 'inactive'; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '已启用' },
  { value: 'inactive', label: '已停用' },
]

/*
 * 列宽一律用百分比：表格是 table-fixed 布局，百分比能精确落到每一列，
 * 不会像 auto 布局那样把剩余空间平均摊给各列，导致表头看起来"飘"在宽列左边。
 */
const columns = computed(() => {
  // 两种角色的列宽都凑满 100%，table-fixed 下才不会有多余空间被二次分配
  // 教师少一列「负责人」，把省下的宽度分给状态/时间/操作，课程列不要独吞
  const titleWidth = isAdmin.value ? 'w-[44%]' : 'w-[40%]'
  const statusWidth = isAdmin.value ? 'w-[14%]' : 'w-[20%]'
  const updatedWidth = isAdmin.value ? 'w-[14%]' : 'w-[20%]'
  const actionsWidth = isAdmin.value ? 'w-[12%]' : 'w-[20%]'

  const list: {
    accessorKey?: string
    id?: string
    header: string
    meta?: { class: { th?: string; td?: string } }
  }[] = [{ accessorKey: 'title', header: '课程', meta: { class: { th: titleWidth } } }]

  // 教师的列表里全是自己的课，再放一列「负责人」只是重复
  if (isAdmin.value) {
    list.push({
      accessorKey: 'teacher_id',
      header: '负责人',
      meta: { class: { th: 'w-[16%]' } },
    })
  }

  list.push(
    {
      accessorKey: 'is_active',
      header: '状态',
      meta: { class: { th: statusWidth } },
    },
    {
      accessorKey: 'updated_at',
      header: '更新时间',
      meta: { class: { th: updatedWidth } },
    },
    { id: 'actions', header: '操作', meta: { class: { th: actionsWidth } } },
  )

  return list
})

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(date)
}

function ownerLabel(course: Course): string {
  if (course.teacher_id === currentUser.value?.id) return '我'
  return course.teacher_display_name
}

function canEdit(course: Course): boolean {
  return isAdmin.value || course.teacher_id === currentUser.value?.id
}

async function loadTeachers(): Promise<void> {
  if (!isAdmin.value) return
  try {
    const data = await listUsers({ role: 'teacher', page_size: 100 })
    teacherOptions.value = data.items
      .filter((user) => user.is_active)
      .map((user) => ({ value: user.id, label: `${user.display_name}（@${user.username}）` }))
  } catch {
    // 教师列表只影响管理员创建/转移课程时的负责人选项
  }
}

async function load(): Promise<void> {
  status.value = 'loading'
  actionError.value = ''

  try {
    const fetchCourses = isAdmin.value ? listCourses : listMyCourses
    const data = await fetchCourses({
      page: page.value,
      page_size: PAGE_SIZE,
      q: keyword.value.trim() || undefined,
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

async function toggleActive(course: Course): Promise<void> {
  actionError.value = ''
  pendingId.value = course.id
  try {
    const updated = await updateCourse(course.id, { is_active: !course.is_active })
    items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (e) {
    actionError.value = e instanceof ApiError ? e.message : '操作失败，请稍后重试。'
  } finally {
    pendingId.value = null
  }
}

function openCreate(): void {
  editing.value = null
  form.code = ''
  form.title = ''
  form.description = ''
  form.teacherId = teacherOptions.value[0]?.value ?? 0
  form.isActive = true
  formError.value = ''
  formOpen.value = true
}

function openEdit(course: Course): void {
  editing.value = course
  form.code = course.code
  form.title = course.title
  form.description = course.description
  form.teacherId = course.teacher_id
  form.isActive = course.is_active
  formError.value = ''
  formOpen.value = true
}

async function submit(): Promise<void> {
  const code = form.code.trim().toUpperCase()
  const title = form.title.trim()
  const description = form.description.trim()

  if (code.length === 0) {
    formError.value = '请填写课程代码'
    return
  }
  if (code.length > 32) {
    formError.value = '课程代码最多 32 位'
    return
  }
  if (!CODE_PATTERN.test(code)) {
    formError.value = '课程代码只能包含大写字母、数字和短横线'
    return
  }
  if (title.length === 0) {
    formError.value = '请填写课程标题'
    return
  }
  if (title.length > 200) {
    formError.value = '课程标题最多 200 个字符'
    return
  }
  if (description.length > 5000) {
    formError.value = '描述最多 5000 个字符'
    return
  }
  if (isAdmin.value && !isEditing.value && form.teacherId < 1) {
    formError.value = '管理员创建课程时必须选择负责人'
    return
  }

  saving.value = true
  formError.value = ''

  try {
    if (editing.value) {
      const original = editing.value
      const payload: CourseUpdatePayload = {}

      if (code !== original.code) payload.code = code
      if (title !== original.title) payload.title = title
      if (description !== original.description) payload.description = description
      if (isAdmin.value && form.teacherId !== original.teacher_id) payload.teacher_id = form.teacherId
      if (form.isActive !== original.is_active) payload.is_active = form.isActive

      // 没有任何改动就不发请求（后端会以 422 拒绝空的 PATCH）
      if (Object.keys(payload).length === 0) {
        formOpen.value = false
        return
      }

      const updated = await updateCourse(original.id, payload)
      items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
    } else {
      await createCourse({
        code,
        title,
        description,
        ...(isAdmin.value ? { teacher_id: form.teacherId } : {}),
      })
      page.value = 1
      await load()
    }

    formOpen.value = false
    if (isAdmin.value) void loadTeachers()
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

function resetAndLoad(): void {
  page.value = 1
  void load()
}

let keywordTimer: number | undefined

watch(keyword, () => {
  window.clearTimeout(keywordTimer)
  keywordTimer = window.setTimeout(resetAndLoad, 300)
})

watch(statusFilter, resetAndLoad)

onMounted(() => {
  void loadTeachers()
  void load()
})
</script>

<template>
  <component :is="layout">
    <div class="toolbar page-toolbar">
      <div class="toolbar__filters">
        <UInput
          v-model="keyword"
          icon="i-lucide-search"
          size="lg"
          placeholder="搜索课程标题"
          aria-label="搜索课程标题"
          class="toolbar__search"
        />
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
        新建课程
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
        caption="课程列表"
        empty="还没有课程，点右上角「新建课程」开始。"
        :ui="{
          base: 'min-w-full table-fixed table-center',
          th: 'h-10 px-3 py-0 text-xs',
          td: 'h-14 px-3 py-0 text-sm text-default',
          tr: 'hover:bg-elevated/50',
        }"
      >
        <template #title-cell="{ row }">
          <div class="course-cell">
            <UIcon name="i-lucide-book-open" class="course-cell__icon" aria-hidden="true" />
            <div class="course-cell__text">
              <p class="course-cell__title">
                {{ row.original.title }}
                <span
                  v-if="isAdmin && row.original.teacher_id === currentUser?.id"
                  class="course-cell__mine"
                >
                  我的
                </span>
              </p>
              <p class="course-cell__code">{{ row.original.code }}</p>
            </div>
          </div>
        </template>

        <template #teacher_id-cell="{ row }">
          <span class="owner-cell">{{ ownerLabel(row.original) }}</span>
        </template>

        <template #is_active-cell="{ row }">
          <div class="status-cell">
            <template v-if="canEdit(row.original)">
              <USwitch
                :model-value="row.original.is_active"
                :disabled="pendingId === row.original.id"
                :aria-label="`${row.original.title} 的启用状态`"
                @update:model-value="toggleActive(row.original)"
              />
              <span class="status-cell__label">
                {{ row.original.is_active ? '启用' : '停用' }}
              </span>
            </template>
            <span v-else class="locked-cell">
              <UIcon name="i-lucide-lock" class="locked-cell__icon" aria-hidden="true" />
              {{ row.original.is_active ? '启用' : '停用' }}
            </span>
          </div>
        </template>

        <template #updated_at-cell="{ row }">
          <span class="date-cell">{{ formatDate(row.original.updated_at) }}</span>
        </template>

        <template #actions-cell="{ row }">
          <UButton
            v-if="canEdit(row.original)"
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
      <p class="table-footer__total">共 <span class="table-footer__count">{{ total }}</span> 门课程</p>
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

    <UModal v-model:open="formOpen" :title="isEditing ? '编辑课程' : '新建课程'">
      <template #body>
        <div class="form">
          <label class="form__field">
            <span class="form__label">课程代码 <span aria-hidden="true">*</span></span>
            <UInput
              v-model="form.code"
              maxlength="32"
              placeholder="例如：MATH101"
              class="w-full"
              @blur="form.code = form.code.trim().toUpperCase()"
            />
          </label>

          <label class="form__field">
            <span class="form__label">标题 <span aria-hidden="true">*</span></span>
            <UInput v-model="form.title" maxlength="200" placeholder="例如：高等数学（上）" class="w-full" />
          </label>

          <label class="form__field">
            <span class="form__label">描述</span>
            <UTextarea
              v-model="form.description"
              :rows="6"
              maxlength="5000"
              placeholder="这门课讲什么、适合谁"
              class="w-full"
              :ui="{ base: 'min-h-[132px]' }"
            />
          </label>

          <label v-if="isAdmin" class="form__field">
            <span class="form__label">负责人<span aria-hidden="true">*</span></span>
            <USelect
              v-model="form.teacherId"
              :items="teacherOptions"
              placeholder="选择一位启用的教师"
              class="w-full"
            />
            <span v-if="!teacherOptions.length" class="form__hint">
              还没有启用的教师，请先在用户管理里把某人设为教师
            </span>
          </label>

          <div v-if="isEditing" class="form__switch">
            <div>
              <p class="form__label">启用课程</p>
              <p class="form__hint">停用后课程和关联资源会从公开目录隐藏</p>
            </div>
            <USwitch v-model="form.isActive" aria-label="是否启用该课程" />
          </div>

          <p v-if="formError" class="form__error" role="alert">{{ formError }}</p>
        </div>
      </template>

      <template #footer>
        <div class="modal-footer">
          <UButton color="neutral" variant="ghost" :disabled="saving" @click="formOpen = false">
            取消
          </UButton>
          <UButton color="primary" :loading="saving" @click="submit">
            {{ isEditing ? '保存修改' : '创建课程' }}
          </UButton>
        </div>
      </template>
    </UModal>
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

/* 工具栏里的控件一律不收缩、不换行：否则中文标签会被挤成两行 */
.toolbar__filters > * {
  flex: none;
  white-space: nowrap;
}

/* 主操作固定在最右，靠 auto 外边距而不是 space-between，   避免左边筛选组被压窄后自己换行 */
.toolbar__primary {
  flex: none;
  margin-left: auto;
  white-space: nowrap;
}

.toolbar__search {
  width: min(100%, 260px);
}

.toolbar__select {
  width: 150px;
}

.action-error {
  margin-bottom: 16px;
}

.course-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.course-cell__icon {
  flex: none;
  width: 18px;
  height: 18px;
  color: var(--lh-primary);
}

.course-cell__text {
  min-width: 0;
}

.course-cell__title {
  margin: 0;
  overflow: hidden;
  color: var(--lh-text);
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.course-cell__mine {
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
  font-size: 11px;
  font-weight: 600;
}

.course-cell__code {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
  line-height: 18px;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
}

.owner-cell {
  color: var(--lh-text);
  font-size: 13px;
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

/* 不可编辑的行：只读文本 + 锁图标，不显示禁用的开关 */
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
  margin: 0;
  color: var(--lh-text);
  font-size: 14px;
  font-weight: 600;
}

.form__hint {
  color: var(--lh-text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.form__switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--lh-border);
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
    flex-wrap: wrap;
    width: 100%;
  }

  .toolbar__primary {
    width: 100%;
  }

  .toolbar__search,
  .toolbar__select {
    width: 100%;
  }
}
</style>
