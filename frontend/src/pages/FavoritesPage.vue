<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { listFavorites, type FavoriteItem } from '../api/favorites'
import { ApiError } from '../api/client'
import { clearSession, useSession } from '../api/session'
import { useFavorites } from '../composables/useFavorites'
import StudentLayout from '../layouts/StudentLayout.vue'
import PageHero from '../components/common/PageHero.vue'
import PageHeader from '../components/common/PageHeader.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorState from '../components/common/ErrorState.vue'
import { navigateCards } from '../components/resources/navigateCards'
import ResourceCard from '../components/resources/ResourceCard.vue'
import ResourceDetailModal from '../components/resources/ResourceDetailModal.vue'
import FavoriteButton from '../components/resources/FavoriteButton.vue'
import type { Resource, ResourceSummary } from '../types/resource'
const { accessToken, isLoggedIn } = useSession()
const favorites = useFavorites()
const items = ref<FavoriteItem[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 18
const loading = ref(false)
const error = ref('')
const requestId = ref('')
const detailOpen = ref(false)
const detailId = ref<number | null>(null)
let sequence = 0
async function load() {
  const seq = ++sequence
  if (!isLoggedIn.value) return
  loading.value = true; error.value = ''; requestId.value = ''
  try {
    const result = await listFavorites(page.value, pageSize)
    if (seq !== sequence) return
    total.value = result.total
    const last = Math.max(1, Math.ceil(total.value / pageSize))
    if (page.value > last) { page.value = last; return }
    items.value = result.items
  } catch (cause) {
    if (seq !== sequence) return
    items.value = []; total.value = 0
    if (cause instanceof ApiError && cause.status === 401) clearSession()
    else { error.value = cause instanceof Error ? cause.message : '收藏加载失败'; requestId.value = cause instanceof ApiError ? cause.requestId : '' }
  } finally { if (seq === sequence) loading.value = false }
}
function summary(resource: Resource): ResourceSummary {
  return {
    id: resource.id, title: resource.title, description: resource.description, resourceType: resource.resource_type,
    courseName: resource.course_title, categoryName: resource.category_name, updatedAt: resource.updated_at, isFavorited: true
  }
}
function showDetail(id: number) { detailId.value = id; detailOpen.value = true }
watch(page, () => { void load() })
watch(favorites.revision, () => { if (isLoggedIn.value) void load() })
watch(accessToken, () => {
  sequence++; items.value = []; total.value = 0; loading.value = false; error.value = ''
  detailOpen.value = false; detailId.value = null
  if (isLoggedIn.value) { if (page.value !== 1) page.value = 1; else void load() }
}, { immediate: true, flush: 'sync' })
onUnmounted(() => { sequence++ })
</script>

<template>
  <StudentLayout>
    <PageHero>
      <PageHeader eyebrow="My Favorites" title="我的收藏" description="保存值得反复阅读的内容，随时继续学习。" />
      <p v-if="isLoggedIn && !error" class="favorites-total">共 <strong>{{ total }}</strong> 份收藏 · 最近收藏在前</p>
    </PageHero>
    <UCard v-if="!isLoggedIn">
      <EmptyState centered title="登录后查看收藏" description="你的收藏会保存在当前账号中。" />
      <div class="mt-5 flex justify-center">
        <UButton :to="{ path: '/login', query: { redirect: '/favorites' } }">前往登录</UButton>
      </div>
    </UCard>
    <ErrorState v-else-if="error" :description="error" :request-id="requestId" @retry="load" />
    <template v-else>
      <div v-if="loading || items.length" class="favorites-grid" :aria-busy="loading" @keydown="navigateCards">
        <template v-if="loading && !items.length">
          <ResourceCard v-for="n in 6" :key="n" loading />
        </template>
        <template v-for="item in items" :key="item.id">
          <ResourceCard v-if="item.resource" :resource="summary(item.resource)" :actions-disabled="loading"
            @open="showDetail(item.resource_id)" />
          <UCard v-else :ui="{ body: 'h-full flex flex-col gap-4' }">
            <UIcon name="i-lucide-file-x" class="size-8 text-muted" />
            <h2 class="font-semibold">资源已失效</h2>
            <p class="text-sm text-muted">资源可能已撤回、归档或暂不可访问，你仍可以取消收藏。</p>
            <div class="mt-auto">
              <FavoriteButton :resource-id="item.resource_id" :favorited="true" :disabled="loading" />
            </div>
          </UCard>
        </template>
      </div>
      <UCard v-else>
        <EmptyState centered icon="i-lucide-bookmark" title="还没有收藏" description="在资源卡片或详情中点击收藏，喜欢的内容就会出现在这里。" />
        <div class="mt-5 flex justify-center">
          <UButton to="/resources">探索资源</UButton>
        </div>
      </UCard>
      <div v-if="total > pageSize" class="mt-6 flex justify-center">
        <UPagination v-model:page="page" :total="total" :items-per-page="pageSize" :disabled="loading" />
      </div>
    </template>
    <ResourceDetailModal v-model:open="detailOpen" :resource-id="detailId" />
  </StudentLayout>
</template>

<style scoped>
.favorites-total {
  margin: 4px 0 12px;
  color: var(--lh-text-secondary);
  font-size: 13px;
}

.favorites-total strong {
  color: var(--lh-primary);
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 1023px) {
  .favorites-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 639px) {
  .favorites-grid {
    grid-template-columns: 1fr;
  }
}
</style>
