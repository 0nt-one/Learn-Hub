<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { listCategories } from '../../api/categories'
import { ApiError } from '../../api/client'
import { listCourses } from '../../api/courses'
import { createResource, updateResource } from '../../api/resources'
import { useSession } from '../../api/session'
import type { Resource, ResourceType } from '../../types/resource'

/*
 * 资源表单弹窗，同时承担新建和编辑：
 * - 新建：POST /resources，结果是 draft（草稿）
 * - 编辑：PATCH /resources/{id}，只有 draft / rejected 能改，带 expected_version 乐观锁
 * 审核提交（POST /resources/{id}/submit）不在这个弹窗里做。
 */
const open = defineModel<boolean>('open', { required: true })
const props = defineProps<{ resource?: Resource | null }>()
const emit = defineEmits<{ saved: [resource: Resource, mode: 'create' | 'edit'] }>()

const { currentUser } = useSession()

const isEdit = computed(() => props.resource != null)
const modalTitle = computed(() => (isEdit.value ? '编辑资源' : '共享新资源'))
const submitLabel = computed(() => (isEdit.value ? '保存修改' : '保存为草稿'))

const TYPE_OPTIONS: { value: ResourceType; label: string }[] = [
  { value: 'document', label: '文档' },
  { value: 'video', label: '视频' },
  { value: 'link', label: '链接' },
]

type FieldKey = 'title' | 'url' | 'duration' | 'pages' | 'course' | 'category'

const FIELD_ELEMENT_IDS: Record<FieldKey, string> = {
  title: 'modal-resource-title',
  url: 'modal-resource-url',
  duration: 'modal-resource-duration',
  pages: 'modal-resource-pages',
  course: 'modal-resource-course',
  category: 'modal-resource-category',
}

const form = reactive({
  title: '',
  description: '',
  resourceType: 'document' as ResourceType,
  url: '',
  // 数字框的 v-model 运行时可能给 number，统一在 @update 里转字符串
  durationMinutes: '',
  pageCount: '',
  courseId: 0,
  categoryId: 0,
})

const fieldErrors = reactive<Record<FieldKey, string>>({
  title: '',
  url: '',
  duration: '',
  pages: '',
  course: '',
  category: '',
})

const courses = ref<{ value: number; label: string }[]>([])
const categories = ref<{ value: number; label: string }[]>([])
const dictionariesLoading = ref(false)
const dictionariesLoaded = ref(false)
const saving = ref(false)
const formError = ref('')

const needsDuration = computed(() => form.resourceType === 'video')
const needsPageCount = computed(() => form.resourceType === 'document')
const noCourses = computed(() => dictionariesLoaded.value && courses.value.length === 0)
const noCategories = computed(() => dictionariesLoaded.value && categories.value.length === 0)
const blocker = computed(() => noCourses.value || noCategories.value)

/** 数字框可能是 number 或空串，统一转字符串再判空 */
function numberText(value: string | number | null | undefined): string {
  return value === null || value === undefined ? '' : String(value).trim()
}

function clearFieldError(key: FieldKey): void {
  fieldErrors[key] = ''
}

function clearAllFieldErrors(): void {
  for (const key of Object.keys(fieldErrors) as FieldKey[]) fieldErrors[key] = ''
}

function resetForm(): void {
  form.title = ''
  form.description = ''
  form.resourceType = 'document'
  form.url = ''
  form.durationMinutes = ''
  form.pageCount = ''
  form.courseId = courses.value[0]?.value ?? 0
  form.categoryId = categories.value[0]?.value ?? 0
  formError.value = ''
  clearAllFieldErrors()
}

/** 预填期间不要触发"切换类型清字段"的逻辑，否则刚填的时长会被清掉 */
let prefilling = false

function prefillFromResource(resource: Resource): void {
  prefilling = true
  form.title = resource.title
  form.description = resource.description
  form.resourceType = resource.resource_type
  form.url = resource.url
  form.durationMinutes =
    resource.duration_seconds == null
      ? ''
      : String(Number((resource.duration_seconds / 60).toFixed(2)))
  form.pageCount = resource.page_count == null ? '' : String(resource.page_count)
  form.courseId = resource.course_id
  form.categoryId = resource.category_id
  formError.value = ''
  clearAllFieldErrors()
  void nextTick(() => {
    prefilling = false
  })
}

async function loadDictionaries(): Promise<void> {
  if (dictionariesLoaded.value || dictionariesLoading.value) return
  dictionariesLoading.value = true
  try {
    const [coursePage, categoryPage] = await Promise.all([
      listCourses({ page: 1, page_size: 100 }),
      listCategories({ page: 1, page_size: 100 }),
    ])
    courses.value = coursePage.items
      .filter((course) => course.is_active)
      .map((course) => ({
        value: course.id,
        // 别人的课程额外标出负责人，避免误投
        label:
          course.teacher_id === currentUser.value?.id
            ? `${course.title}（${course.code}）`
            : `${course.title}（${course.code}） @${course.teacher_display_name}`,
      }))
    categories.value = categoryPage.items
      .filter((category) => category.is_active)
      .map((category) => ({ value: category.id, label: category.name }))

    dictionariesLoaded.value = true
    if (!form.courseId) form.courseId = courses.value[0]?.value ?? 0
    if (!form.categoryId) form.categoryId = categories.value[0]?.value ?? 0
  } catch (e) {
    formError.value = e instanceof ApiError ? e.message : '课程和分类加载失败，请重试。'
  } finally {
    dictionariesLoading.value = false
  }
}

function validate(): boolean {
  clearAllFieldErrors()

  const title = form.title.trim()
  if (!title) fieldErrors.title = '请填写资源标题'
  else if (title.length > 200) fieldErrors.title = '标题最多 200 个字符'

  const url = form.url.trim()
  if (!url) {
    fieldErrors.url = '请填写资源地址'
  } else {
    try {
      const parsed = new URL(url)
      if (parsed.protocol !== 'https:') fieldErrors.url = '地址必须以 https:// 开头'
      else if (parsed.username || parsed.password) fieldErrors.url = '地址不能包含用户名或密码'
    } catch {
      fieldErrors.url = '地址不是合法链接'
    }
  }

  if (form.resourceType === 'video') {
    const text = numberText(form.durationMinutes)
    const minutes = Number(text)
    if (!text) fieldErrors.duration = '请填写视频时长'
    else if (!Number.isFinite(minutes) || minutes <= 0) fieldErrors.duration = '时长必须大于 0'
  }

  if (form.resourceType === 'document') {
    const text = numberText(form.pageCount)
    const pages = Number(text)
    if (text && (!Number.isInteger(pages) || pages <= 0)) {
      fieldErrors.pages = '页数必须是大于 0 的整数'
    }
  }

  if (!form.courseId) fieldErrors.course = '请选择所属课程'
  if (!form.categoryId) fieldErrors.category = '请选择分类'

  return Object.values(fieldErrors).every((message) => !message)
}

function focusFirstError(): void {
  const firstKey = (Object.keys(fieldErrors) as FieldKey[]).find((key) => fieldErrors[key])
  if (!firstKey) return
  document.getElementById(FIELD_ELEMENT_IDS[firstKey])?.focus()
}

async function submit(): Promise<void> {
  formError.value = ''

  if (!validate()) {
    formError.value = '还有必填项没填好，已标红。'
    focusFirstError()
    return
  }

  const payload = {
    title: form.title.trim(),
    description: form.description.trim(),
    resource_type: form.resourceType,
    url: form.url.trim(),
    duration_seconds:
      form.resourceType === 'video'
        ? Math.round(Number(numberText(form.durationMinutes)) * 60)
        : null,
    page_count:
      form.resourceType === 'document' && numberText(form.pageCount)
        ? Number(numberText(form.pageCount))
        : null,
    course_id: form.courseId,
    category_id: form.categoryId,
  }

  saving.value = true
  try {
    if (props.resource) {
      const updated = await updateResource(props.resource.id, {
        ...payload,
        expected_version: props.resource.version_id,
      })
      open.value = false
      emit('saved', updated, 'edit')
    } else {
      const created = await createResource(payload)
      open.value = false
      emit('saved', created, 'create')
    }
  } catch (e) {
    if (e instanceof ApiError && e.code === 'VERSION_CONFLICT') {
      formError.value = '这条资源已被修改（可能是别的标签页），请关闭弹窗刷新后重试。'
    } else if (e instanceof ApiError && e.code === 'INVALID_STATE') {
      formError.value = '当前状态不能编辑：只有草稿和被驳回的资源可以修改。'
    } else {
      formError.value = e instanceof ApiError ? e.message : '保存失败，请稍后重试。'
    }
  } finally {
    saving.value = false
  }
}

// 切换类型时清掉另一类型的专属字段，避免被后端以 422 拒绝
watch(
  () => form.resourceType,
  (type) => {
    if (prefilling) return
    if (type !== 'video') {
      form.durationMinutes = ''
      clearFieldError('duration')
    }
    if (type !== 'document') {
      form.pageCount = ''
      clearFieldError('pages')
    }
  },
)

// 每次打开都刷新字典（课程可能刚被创建），并按模式重置或预填
watch(open, (isOpen) => {
  if (!isOpen) return
  dictionariesLoaded.value = false

  const editing = props.resource
  if (editing) {
    prefillFromResource(editing)
    void loadDictionaries()
  } else {
    resetForm()
    void loadDictionaries().then(() => {
      if (!form.courseId) form.courseId = courses.value[0]?.value ?? 0
      if (!form.categoryId) form.categoryId = categories.value[0]?.value ?? 0
    })
  }
})
</script>

<template>
  <UModal v-model:open="open" :title="modalTitle" scrollable>
    <template #body>
      <UAlert
        v-if="noCourses"
        color="warning"
        variant="soft"
        icon="i-lucide-triangle-alert"
        title="暂无可用课程"
        description="资源必须归属一门启用课程，请联系教师或管理员创建课程。"
        class="modal-blocker"
      />
      <UAlert
        v-else-if="noCategories"
        color="warning"
        variant="soft"
        icon="i-lucide-triangle-alert"
        title="没有可用的分类"
        description="分类由管理员维护，请让管理员先创建分类。"
        class="modal-blocker"
      />

      <form class="form" novalidate @submit.prevent="submit">
        <UAlert
          v-if="formError"
          color="error"
          variant="soft"
          icon="i-lucide-circle-alert"
          :title="formError"
        />

        <div class="form__field">
          <label class="form__label" for="modal-resource-title">
            标题 <span class="form__required" aria-hidden="true">*</span>
          </label>
          <UInput
            id="modal-resource-title"
            v-model="form.title"
            maxlength="200"
            placeholder="例如：高等数学第一章课件"
            class="w-full"
            :color="fieldErrors.title ? 'error' : undefined"
            @update:model-value="clearFieldError('title')"
          />
          <p v-if="fieldErrors.title" class="form__error-text">{{ fieldErrors.title }}</p>
        </div>

        <div class="form__field">
          <label class="form__label" for="modal-resource-description">描述</label>
          <UTextarea
            id="modal-resource-description"
            v-model="form.description"
            :rows="4"
            maxlength="5000"
            placeholder="这份资源包含什么、适合哪个阶段使用"
            class="w-full"
          />
        </div>

        <!-- 资源类型和分类都是短标签，共用一行；课程名较长，单独通栏 -->
        <div class="form__row">
          <div class="form__field">
            <label class="form__label" for="modal-resource-type">
              资源类型 <span class="form__required" aria-hidden="true">*</span>
            </label>
            <USelect
              id="modal-resource-type"
              v-model="form.resourceType"
              :items="TYPE_OPTIONS"
              class="w-full"
            />
          </div>

          <div class="form__field">
            <label class="form__label" for="modal-resource-category">
              分类 <span class="form__required" aria-hidden="true">*</span>
            </label>
            <USelect
              id="modal-resource-category"
              v-model="form.categoryId"
              :items="categories"
              :loading="dictionariesLoading"
              placeholder="选择分类"
              class="w-full"
              :color="fieldErrors.category ? 'error' : undefined"
              @update:model-value="clearFieldError('category')"
            />
            <p v-if="fieldErrors.category" class="form__error-text">{{ fieldErrors.category }}</p>
          </div>
        </div>

        <!-- 数值类字段只有视频/文档才有，占半栏即可 -->
        <div v-if="needsDuration || needsPageCount" class="form__row">
          <div v-if="needsDuration" class="form__field">
            <label class="form__label" for="modal-resource-duration">
              时长（分钟）<span class="form__required" aria-hidden="true">*</span>
            </label>
            <UInput
              id="modal-resource-duration"
              :model-value="form.durationMinutes"
              type="number"
              min="1"
              step="1"
              placeholder="例如：45"
              class="w-full"
              :color="fieldErrors.duration ? 'error' : undefined"
              @update:model-value="(value) => { form.durationMinutes = String(value ?? ''); clearFieldError('duration') }"
            />
            <p v-if="fieldErrors.duration" class="form__error-text">{{ fieldErrors.duration }}</p>
          </div>

          <div v-else class="form__field">
            <label class="form__label" for="modal-resource-pages">页数</label>
            <UInput
              id="modal-resource-pages"
              :model-value="form.pageCount"
              type="number"
              min="1"
              step="1"
              placeholder="选填，例如：32"
              class="w-full"
              :color="fieldErrors.pages ? 'error' : undefined"
              @update:model-value="(value) => { form.pageCount = String(value ?? ''); clearFieldError('pages') }"
            />
            <p v-if="fieldErrors.pages" class="form__error-text">{{ fieldErrors.pages }}</p>
          </div>
        </div>

        <div class="form__field">
          <label class="form__label" for="modal-resource-url">
            资源地址 <span class="form__required" aria-hidden="true">*</span>
          </label>
          <UInput
            id="modal-resource-url"
            v-model="form.url"
            type="url"
            maxlength="2048"
            placeholder="https://"
            class="w-full"
            :color="fieldErrors.url ? 'error' : undefined"
            @update:model-value="clearFieldError('url')"
          />
          <p v-if="fieldErrors.url" class="form__error-text">{{ fieldErrors.url }}</p>
        </div>

        <!-- 课程选项带「课程名（代码） @负责人」，半栏放不下会被裁掉，所以各占整行 -->
        <div class="form__field">
          <label class="form__label" for="modal-resource-course">
            所属课程 <span class="form__required" aria-hidden="true">*</span>
          </label>
          <USelect
            id="modal-resource-course"
            v-model="form.courseId"
            :items="courses"
            :loading="dictionariesLoading"
            placeholder="选择课程"
            class="w-full"
            :color="fieldErrors.course ? 'error' : undefined"
            @update:model-value="clearFieldError('course')"
          />
          <p v-if="fieldErrors.course" class="form__error-text">{{ fieldErrors.course }}</p>
        </div>
      </form>
    </template>

    <template #footer>
      <div class="modal-footer">
        <UButton color="neutral" variant="ghost" :disabled="saving" @click="open = false">
          取消
        </UButton>
        <!-- 没有可用课程/分类时不显示保存按钮，只留提示条说明原因 -->
        <UButton
          v-if="!blocker"
          color="primary"
          :loading="saving"
          :disabled="dictionariesLoading"
          @click="submit"
        >
          {{ submitLabel }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>

<style scoped>
.modal-blocker {
  margin-bottom: 16px;
}

.form {
  display: grid;
  gap: 16px;
}

.form__row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form__field {
  display: grid;
  gap: 6px;
  min-width: 0;
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

@media (max-width: 767px) {
  .form__row {
    grid-template-columns: 1fr;
  }
}
</style>
