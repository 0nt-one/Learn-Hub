<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listResources } from '../api/resources'
import { listCourses } from '../api/courses'
import { listFavorites } from '../api/favorites'
import { listLearningRecords } from '../api/learning'
import { useSession } from '../api/session'
import { useFavorites } from '../composables/useFavorites'
import BaseCard from '../components/common/BaseCard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import campusBanner from '../../../docs/images/湖畔校园的明日寄语.png'
import ResourceDetailModal from '../components/resources/ResourceDetailModal.vue'
import ResourceTypeBadge from '../components/resources/ResourceTypeBadge.vue'
import StudentLayout from '../layouts/StudentLayout.vue'
import type { ResourceType } from '../types/resource'

interface HomeItem {
  id: number
  title: string
  subtitle?: string
  description?: string
  type?: ResourceType
  progress?: number
  unavailable?: boolean
}

const router = useRouter()
const { accessToken, isLoggedIn } = useSession()
const keyword = ref('')
const favorites = useFavorites()
const selected = ref<HomeItem | null>(null)
const detailOpen = ref(false)
const sections = [
  { key: 'latest', title: '最新资源', icon: 'i-lucide-sparkles', to: '/resources', empty: '暂时没有已发布的资源。' },
  { key: 'courses', title: '课程探索', icon: 'i-lucide-library', to: '/resources', empty: '暂时没有可浏览的课程。' },
  { key: 'learning', title: '继续学习', icon: 'i-lucide-circle-play', to: '/learning', empty: '打开一份资源并记录进度，就能从这里继续。' },
  { key: 'favorites', title: '最近收藏', icon: 'i-lucide-bookmark', to: '/favorites', empty: '收藏的资源会出现在这里。' },
] as const
type SectionKey = typeof sections[number]['key']
const state = reactive<Record<SectionKey, { items: HomeItem[]; loading: boolean; error: string }>>({
  latest: { items: [], loading: false, error: '' },
  courses: { items: [], loading: false, error: '' },
  learning: { items: [], loading: false, error: '' },
  favorites: { items: [], loading: false, error: '' },
})
const loaders: Record<SectionKey, () => Promise<HomeItem[]>> = {
  latest: async () => (await listResources({ page: 1, page_size: 3, sort: 'newest' })).items.map(item => ({
    id: item.id, title: item.title, subtitle: item.course_title, type: item.resource_type, description: item.description,
  })),
  courses: async () => (await listCourses({ page: 1, page_size: 3, is_active: true })).items.map(item => ({
    id: item.id, title: item.title, subtitle: item.code,
  })),
  learning: async () => (await listLearningRecords(1, 3)).items.map(item => ({
    id: item.resource_id, title: item.resource.title, subtitle: item.resource.course_title,
    type: item.resource.resource_type, progress: item.progress, unavailable: !item.resource.is_available,
  })),
  favorites: async () => (await listFavorites(1, 3)).items.map(item => ({
    id: item.resource_id, title: item.resource?.title ?? '资源暂不可用',
    subtitle: item.resource?.course_title ?? ('资源 #' + item.resource_id),
    type: item.resource?.resource_type, unavailable: !item.resource,
  })),
}
const requests = { latest: 0, courses: 0, learning: 0, favorites: 0 }
const currentProgress = computed(() => state.learning.items.find(item => item.id === selected.value?.id)?.progress)

async function load(key: SectionKey) {
  const token = accessToken.value
  if (!token) return
  const request = ++requests[key]
  const section = state[key]
  section.loading = true
  section.error = ''
  try {
    const items = await loaders[key]()
    if (request === requests[key] && token === accessToken.value) section.items = items
  } catch (cause) {
    if (request === requests[key] && token === accessToken.value) {
      section.error = cause instanceof Error ? cause.message : '加载失败，请重试。'
    }
  } finally {
    if (request === requests[key]) section.loading = false
  }
}

function search() {
  const q = keyword.value.trim()
  void router.push({ path: '/resources', query: q ? { q } : {} })
}

function openResource(item: HomeItem) {
  selected.value = item
  detailOpen.value = true
}

watch(accessToken, () => {
  detailOpen.value = false
  selected.value = null
  for (const { key } of sections) {
    requests[key]++
    Object.assign(state[key], { items: [], loading: false, error: '' })
    if (accessToken.value) void load(key)
  }
}, { immediate: true, flush: 'sync' })
watch(favorites.revision, () => { void load('favorites') })
onUnmounted(() => {
  for (const { key } of sections) requests[key]++
})
</script>

<template>
  <StudentLayout>
    <section class="hero" aria-labelledby="hero-title" :style="{ backgroundImage: 'url(' + campusBanner + ')' }">
      <div class="hero__content">
        <p class="hero__eyebrow">LEARN-HUB</p>
        <h1 id="hero-title">探索更大的<span>学习世界</span></h1>
        <p class="hero__description">按课程找资料，把想学的内容收藏起来，随时接着学。</p>
        <form class="hero__search" role="search" @submit.prevent="search">
          <UInput v-model="keyword" type="search" maxlength="100" icon="i-lucide-search" size="lg" aria-label="搜索资源标题"
            placeholder="搜索资源标题" class="min-w-0 flex-1" />
          <UButton type="submit" size="lg">搜索</UButton>
        </form>
      </div>
    </section>

    <div v-if="isLoggedIn" class="home-grid">
      <BaseCard v-for="section in sections" :key="section.key" :class="'home-panel--' + section.key" density="compact"
        title-size="md">
        <template #title>
          <h2 class="home-panel__title">
            <UIcon :name="section.icon" aria-hidden="true" />{{ section.title }}
          </h2>
        </template>
        <template #action>
          <UButton :to="section.to" variant="link" size="sm" class="shrink-0" :aria-label="'查看全部' + section.title"
            trailing-icon="i-lucide-arrow-right">查看全部</UButton>
        </template>
        <ErrorState v-if="state[section.key].error" :description="state[section.key].error"
          @retry="load(section.key)" />
        <div v-else-if="state[section.key].loading" class="space-y-3" role="status" aria-label="加载中">
          <USkeleton v-for="n in 3" :key="n" class="h-10 w-full" />
        </div>
        <ul v-else-if="state[section.key].items.length" class="home-list" :class="'home-list--' + section.key">
          <li v-for="(item, index) in state[section.key].items" :key="item.id">
            <RouterLink v-if="section.key === 'courses'" class="home-row"
              :to="{ path: '/resources', query: { course_id: item.id } }">
              <UIcon name="i-lucide-book-open" class="home-row__icon" />
              <span class="home-row__content"><strong>{{ item.title }}</strong><small>{{ item.subtitle }}</small></span>
            </RouterLink>
            <button v-else-if="section.key === 'latest' && index === 0" type="button" class="home-feature"
              @click="openResource(item)">
              <ResourceTypeBadge v-if="item.type" :type="item.type" />
              <strong class="line-clamp-2">{{ item.title }}</strong>
              <span v-if="item.description" class="home-feature__description line-clamp-2">{{ item.description }}</span>
              <span class="home-feature__footer"><span>{{ item.subtitle }}</span>
                <UIcon name="i-lucide-arrow-right" aria-hidden="true" />
              </span>
            </button>
            <component :is="item.unavailable ? 'div' : 'button'" v-else :type="item.unavailable ? undefined : 'button'"
              class="home-row" @click="!item.unavailable && openResource(item)">
              <ResourceTypeBadge v-if="item.type" :type="item.type" class="shrink-0" />
              <span class="home-row__content">
                <strong>{{ item.title }}</strong>
                <small v-if="item.subtitle">{{ item.subtitle }}</small>
                <progress v-if="!item.unavailable && item.progress !== undefined" :value="item.progress" max="100"
                  aria-label="学习进度" />
              </span>
              <span v-if="item.unavailable" class="shrink-0 text-xs text-muted">暂不可用</span>
              <span v-else-if="item.progress !== undefined" class="shrink-0 text-sm text-primary">{{ item.progress
                }}%</span>
              <UIcon v-else name="i-lucide-chevron-right" class="shrink-0" />
            </component>
          </li>
        </ul>
        <p v-else class="home-empty">{{ section.empty }}</p>
      </BaseCard>
    </div>
    <UCard v-else class="mt-5">
      <div class="guest-panel">
        <div>
          <h2 class="font-semibold">登录后开启学习</h2>
          <p class="mt-1 text-sm text-muted">浏览课程资源、收藏资料，并保存学习进度。</p>
        </div>
        <UButton to="/login">登录</UButton>
      </div>
    </UCard>
    <ResourceDetailModal v-model:open="detailOpen" :resource-id="selected?.id ?? null"
      :initial-progress="currentProgress" @saved="load('learning')" />
  </StudentLayout>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  aspect-ratio: 3 / 1;
  padding: clamp(30px, 3vw, 60px);
  overflow: hidden;
  border-radius: 20px;
  background-position: center;
  background-size: cover;
}

.hero__content {
  min-width: 0;
  max-width: min(100%, 560px);
}

.hero__eyebrow {
  color: var(--lh-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .12em;
}

.hero h1 {
  margin: 8px 0 0;
  font-size: clamp(60px, 4vw, 70px);
  font-weight: 700;
  line-height: 1.16;
  color: var(--lh-text);
}

.hero h1 span {
  color: var(--lh-primary);
}

.hero__description {
  margin: 12px 0 20px;
  color: var(--lh-text-secondary);
}

.hero__search {
  display: flex;
  gap: 8px;
  max-width: 600px;
}

.home-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) repeat(2, minmax(0, 1fr));
  grid-template-areas: 'latest courses courses' 'latest learning favorites';
  grid-template-rows: auto 1fr;
  gap: 16px;
  margin-top: 20px;
}

.home-grid>* {
  min-width: 0;
}

.home-panel--latest {
  grid-area: latest;
}

.home-panel--courses {
  grid-area: courses;
}

.home-panel--learning {
  grid-area: learning;
}

.home-panel--favorites {
  grid-area: favorites;
}

.home-panel__title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.home-panel__title>span {
  color: var(--lh-primary);
}

.home-list {
  display: grid;
  gap: 4px;
}

.home-list>li {
  min-width: 0;
}

.home-list--courses {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.home-list--courses .home-row {
  min-height: 74px;
  background: var(--lh-surface-subtle);
}

.home-list--courses .home-row:hover {
  background: var(--lh-primary-soft);
}

.home-feature {
  display: grid;
  justify-items: start;
  align-content: center;
  gap: 10px;
  width: 100%;
  min-height: 200px;
  padding: 20px;
  border-radius: 12px;
  background: var(--lh-primary-soft);
  text-align: left;
  cursor: pointer;
}

.home-feature:hover {
  box-shadow: inset 0 0 0 1px var(--lh-primary-border);
}

.home-feature strong {
  font-size: clamp(20px, 2vw, 28px);
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.home-feature__description {
  font-size: 14px;
  color: var(--lh-text-secondary);
  overflow-wrap: anywhere;
}

.home-feature__footer {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--lh-primary);
}

.home-feature__footer>span:first-child {
  min-width: 0;
  overflow-wrap: anywhere;
}

.home-row {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 10px;
  text-align: left;
  border-radius: 8px;
}

:is(a, button).home-row:hover {
  background: var(--lh-surface-subtle);
}

.home-row__content {
  display: grid;
  flex: 1;
  min-width: 0;
  gap: 3px;
}

.home-row__content strong,
.home-row__content small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-row__content strong {
  font-size: 14px;
  font-weight: 600;
}

.home-row__content progress {
  width: 100%;
  height: 5px;
  accent-color: var(--lh-primary);
}

.home-row__content small,
.home-empty {
  font-size: 13px;
  color: var(--lh-text-secondary);
}

.home-row__icon {
  color: var(--lh-primary);
  flex-shrink: 0;
}

.guest-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

@media (max-width: 1023px) {
  .home-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-areas: 'latest courses' 'learning favorites';
  }

  .home-list--courses {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 767px) {
  .hero {
    padding: 18px 16px;
    background-position: left center;
  }

  .hero h1 {
    font-size: clamp(22px, 5vw, 32px);
  }

  .hero__description {
    margin: 8px 0 12px;
    font-size: 14px;
  }

  .home-grid {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: 'learning' 'latest' 'courses' 'favorites';
  }
}
</style>
