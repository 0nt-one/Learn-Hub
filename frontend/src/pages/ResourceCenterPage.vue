<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listResources, type ResourceListParams } from '../api/resources'
import { listCourses } from '../api/courses'
import { listCategories } from '../api/categories'
import { ApiError } from '../api/client'
import { clearSession, useSession } from '../api/session'
import { usePagedOptions } from '../composables/usePagedOptions'
import { catalogQuery, parseCatalogQuery } from '../router/catalogQuery'
import PageHeader from '../components/common/PageHeader.vue'
import HeroIllustration from '../components/illustrations/HeroIllustration.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorState from '../components/common/ErrorState.vue'
import { navigateCards } from '../components/resources/navigateCards'
import ResourceCard from '../components/resources/ResourceCard.vue'
import ResourceFilterPanel from '../components/resources/ResourceFilterPanel.vue'
import ResourceToolbar from '../components/resources/ResourceToolbar.vue'
import ResourceDetailModal from '../components/resources/ResourceDetailModal.vue'
import StudentLayout from '../layouts/StudentLayout.vue'
import type { Resource, ResourceFilters, ResourceSummary } from '../types/resource'

const route = useRoute()
const router = useRouter()
const { accessToken, isLoggedIn } = useSession()
const params = computed(() => parseCatalogQuery(route.query))
const keyword = ref('')
const view = ref<'grid' | 'list'>('grid')
const items = ref<Resource[]>([])
const total = ref<number | null>(null)
const loading = ref(false)
const error = ref('')
const requestId = ref('')
const filterOpen = ref(false)
const detailOpen = ref(false)
const detailId = ref<number | null>(null)
const blankFilters = (): ResourceFilters => ({ courseId: null, categoryId: null, type: null })
const draft = ref<ResourceFilters>(blankFilters())
let sequence = 0

const loginTarget = computed(() => ({ path: '/login', query: { redirect: route.fullPath } }))
function expireSession() { clearSession() }
const courseOptions = usePagedOptions(
  page => listCourses({ page, page_size: 100, is_active: true }), expireSession)
const categoryOptions = usePagedOptions(
  page => listCategories({ page, page_size: 100, is_active: true }), expireSession)
const filterProps = computed(() => ({
  courses: courseOptions.items.value, categories: categoryOptions.items.value,
  coursesMore: courseOptions.more.value, categoriesMore: categoryOptions.more.value,
  coursesLoading: courseOptions.loading.value, categoriesLoading: categoryOptions.loading.value,
  coursesError: courseOptions.error.value, categoriesError: categoryOptions.error.value,
}))
const filters = computed<ResourceFilters>(() => ({
  courseId: params.value.course_id ?? null,
  categoryId: params.value.category_id ?? null,
  type: params.value.resource_type ?? null,
}))
const typeNames = { document: '文档', video: '视频', link: '链接' }
const chips = computed(() => [
  ...(params.value.q ? [{ key: 'q', label: `标题：${params.value.q}` }] : []),
  ...(params.value.course_id ? [{ key: 'course_id', label: courseOptions.items.value.find(c => c.id === params.value.course_id)?.title ?? `课程 #${params.value.course_id}` }] : []),
  ...(params.value.category_id ? [{ key: 'category_id', label: categoryOptions.items.value.find(c => c.id === params.value.category_id)?.name ?? `分类 #${params.value.category_id}` }] : []),
  ...(params.value.resource_type ? [{ key: 'resource_type', label: typeNames[params.value.resource_type] }] : []),
])

function change(patch: Partial<ResourceListParams>) {
  void router.push({ path: '/resources', query: catalogQuery({ ...params.value, page: 1, ...patch }) })
}
function changeFilters(value: ResourceFilters) {
  change({ course_id: value.courseId ?? undefined, category_id: value.categoryId ?? undefined, resource_type: value.type ?? undefined })
}
function clearFilters() {
  keyword.value = ''
  change({ q: undefined, course_id: undefined, category_id: undefined, resource_type: undefined })
}
function submitSearch(event: Event) {
  if (event instanceof KeyboardEvent && event.isComposing) return
  change({ q: keyword.value.trim().slice(0, 100) || undefined })
}
function showFilters() { draft.value = { ...filters.value }; filterOpen.value = true }
function applyFilters() { changeFilters(draft.value); filterOpen.value = false }
function summary(resource: Resource): ResourceSummary {
  return {
    id: resource.id, title: resource.title, description: resource.description,
    resourceType: resource.resource_type, courseName: resource.course_title,
    categoryName: resource.category_name, updatedAt: resource.updated_at, isFavorited: resource.is_favorited,
  }
}
function showResource(resource: Resource) { detailId.value = resource.id; detailOpen.value = true }

async function load() {
  const current = ++sequence
  if (!isLoggedIn.value) return
  loading.value = true
  error.value = ''
  requestId.value = ''
  detailOpen.value = false
  try {
    const data = await listResources(params.value)
    if (current !== sequence) return
    const lastPage = Math.max(1, Math.ceil(data.total / (params.value.page_size ?? 20)))
    if ((params.value.page ?? 1) > lastPage) {
      await router.replace({ path: '/resources', query: catalogQuery({ ...params.value, page: lastPage }) })
      return
    }
    items.value = data.items
    total.value = data.total
  } catch (cause) {
    if (current !== sequence) return
    items.value = []
    total.value = null
    if (cause instanceof ApiError && cause.status === 401) expireSession()
    else {
      error.value = cause instanceof ApiError ? cause.message : '资源加载失败，请稍后重试。'
      requestId.value = cause instanceof ApiError ? cause.requestId : ''
    }
  } finally {
    if (current === sequence) loading.value = false
  }
}

watch(accessToken, () => {
  sequence++
  items.value = []
  total.value = null
  error.value = ''
  loading.value = false
  detailOpen.value = false
  filterOpen.value = false
  courseOptions.reset()
  categoryOptions.reset()
  if (isLoggedIn.value) {
    void courseOptions.loadMore()
    void categoryOptions.loadMore()
  }
}, { immediate: true, flush: 'sync' })

watch([() => route.fullPath, accessToken], () => {
  sequence++
  keyword.value = params.value.q ?? ''
  const canonical = catalogQuery(params.value)
  if (JSON.stringify(route.query) !== JSON.stringify(canonical)) {
    void router.replace({ path: '/resources', query: canonical })
    return
  }
  void load()
}, { immediate: true })
onUnmounted(() => { sequence++ })
</script>

<template>
  <StudentLayout>
    <div class="catalog-heading">
      <PageHeader eyebrow="Resource Center" title="资源中心" description="按课程、分类和类型探索学习资源，找到适合你的内容。" />
      <HeroIllustration class="catalog-heading__illustration" />
    </div>

    <UCard v-if="!isLoggedIn" class="catalog-login">
      <EmptyState title="登录后探索学习资源" description="这里汇集已发布的课程资源，登录后可以搜索和筛选。" icon="i-lucide-library" />
      <UButton :to="loginTarget" class="mt-5">前往登录</UButton>
    </UCard>

    <div v-else class="catalog">
      <aside class="catalog__aside">
        <ResourceFilterPanel :model-value="filters" v-bind="filterProps" @update:model-value="changeFilters"
          @reset="changeFilters(blankFilters())" @load-courses="courseOptions.loadMore"
          @load-categories="categoryOptions.loadMore" />
      </aside>
      <div class="catalog__main">
        <form class="catalog__search" role="search" @submit.prevent="submitSearch"
          @keydown.enter="($event.isComposing || $event.keyCode === 229) && $event.preventDefault()">
          <label for="resource-search">搜索资源标题</label>
          <div class="catalog__search-row">
            <UInput id="resource-search" v-model="keyword" icon="i-lucide-search" maxlength="100" size="lg"
              placeholder="输入资源标题关键词" class="catalog__search-input" />
            <UButton type="submit" size="lg" :loading="loading">搜索</UButton>
            <UButton type="button" class="catalog__filter-button" icon="i-lucide-sliders-horizontal" color="neutral"
              variant="outline" size="lg" @click="showFilters">筛选</UButton>
          </div>
        </form>

        <div v-if="chips.length" class="catalog__chips">
          <UButton v-for="chip in chips" :key="chip.key" color="primary" variant="soft" size="xs"
            trailing-icon="i-lucide-x" :aria-label="`移除筛选：${chip.label}`" @click="change({ [chip.key]: undefined })">{{
              chip.label }}</UButton>
          <UButton color="neutral" variant="link" size="xs" @click="clearFilters">清空筛选</UButton>
        </div>

        <ResourceToolbar :total="total" :sort="params.sort ?? 'newest'" :loading="loading" :view="view"
          @update:sort="change({ sort: $event })" @update:view="view = $event" />
        <ErrorState v-if="error" :description="error" :request-id="requestId" @retry="load" />

        <div v-if="loading || items.length" :aria-busy="loading"
          :class="['catalog__results', { 'catalog__results--list': view === 'list' }]" @keydown="navigateCards">
          <template v-if="loading && !items.length">
            <ResourceCard v-for="n in 9" :key="n" :view="view" loading />
          </template>
          <ResourceCard v-for="resource in items" :key="resource.id" :resource="summary(resource)" :view="view"
            :actions-disabled="loading" @open="showResource(resource)" />
        </div>
        <UCard v-else-if="!error" :ui="{ body: 'flex flex-col items-center gap-5 py-12 sm:py-12 text-center' }">
          <EmptyState centered :title="chips.length ? '没有找到匹配的资源' : '还没有已发布的资源'"
            :description="chips.length ? '试试其他关键词，或减少筛选条件。' : '资源审核发布后会出现在这里。'" icon="i-lucide-search-x" />
          <UButton v-if="chips.length" variant="outline" @click="clearFilters">清空筛选</UButton>
        </UCard>

        <footer v-if="total !== null && total > 0" class="catalog__pagination">
          <span>共 {{ total }} 条资源</span>
          <UPagination :page="params.page ?? 1" :total="total" :items-per-page="params.page_size ?? 20"
            :sibling-count="0" :show-edges="false" @update:page="change({ page: $event })" />
          <USelect aria-label="每页条数" :model-value="params.page_size ?? 20"
            :items="[{ label: '20 条 / 页', value: 20 }, { label: '40 条 / 页', value: 40 }]"
            @update:model-value="change({ page_size: $event })" />
        </footer>
      </div>
    </div>

    <USlideover v-model:open="filterOpen" title="筛选资源" description="选择条件后点击应用筛选。" side="right">
      <template #body>
        <ResourceFilterPanel v-model="draft" v-bind="filterProps" @reset="draft = blankFilters()"
          @load-courses="courseOptions.loadMore" @load-categories="categoryOptions.loadMore" />
      </template>
      <template #footer>
        <UButton block @click="applyFilters">应用筛选</UButton>
      </template>
    </USlideover>
    <ResourceDetailModal v-model:open="detailOpen" :resource-id="detailId" />

  </StudentLayout>
</template>

<style scoped>
.catalog-heading { display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, 36%); align-items: center; min-height: 210px; padding: 16px 40px; margin: 0 -16px 24px; overflow: hidden; border-radius: 20px; background: var(--lh-primary-soft); }
.catalog-heading :deep(.page-header) { min-width: 0; margin: 0; padding: 20px 0; }
.catalog-heading__illustration { justify-self: end; width: 100%; max-width: 500px; height: 245px; pointer-events: none; }
@media (max-width: 767px) {
  .catalog-heading { grid-template-columns: minmax(0, 1fr) 32%; min-height: 160px; padding: 16px 20px; margin-inline: 0; gap: 8px; }
  .catalog-heading__illustration { height: auto; }
}
@media (max-width: 479px) {
  .catalog-heading { grid-template-columns: minmax(0, 1fr); min-height: 140px; }
  .catalog-heading__illustration { display: none; }
}

.catalog {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.catalog__aside {
  position: sticky;
  top: calc(var(--lh-header-height) + 16px);
  max-height: calc(100svh - var(--lh-header-height) - 32px);
  overflow-y: auto;
}

.catalog__main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.catalog__search {
  display: grid;
  gap: 10px;
  padding: 20px;
  background: var(--lh-surface);
  border: 1px solid var(--lh-border);
  border-radius: 12px;
}

.catalog__search label {
  font-size: 14px;
  font-weight: 600;
}

.catalog__search-row {
  display: flex;
  gap: 12px;
}

.catalog__search-input {
  flex: 1;
  min-width: 0;
}

.catalog__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.catalog__chips :deep(button) {
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

.catalog__results {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.catalog__results--list {
  grid-template-columns: 1fr;
  gap: 10px;
}
@media (min-width: 768px) and (max-width: 1199px) {
  .catalog__results:not(.catalog__results--list) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

.catalog__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: var(--lh-text-secondary);
}

.catalog__filter-button {
  display: none;
}

@media (max-width: 1023px) {
  .catalog {
    grid-template-columns: 1fr;
  }

  .catalog__aside {
    display: none;
  }

  .catalog__filter-button {
    display: inline-flex;
  }
}

@media (max-width: 767px) {

  .catalog__results {
    grid-template-columns: 1fr;
  }

  .catalog__search {
    padding: 16px;
  }

  .catalog__search-row {
    flex-wrap: wrap;
  }

  .catalog__search-input {
    flex-basis: 100%;
  }

  .catalog__pagination {
    justify-content: center;
  }
}


</style>
