<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { listLearningRecords } from '../api/learning'
import { ApiError } from '../api/client'
import { clearSession, useSession } from '../api/session'
import type { LearningRecordItem } from '../types/learning'
import StudentLayout from '../layouts/StudentLayout.vue'
import PageHero from '../components/common/PageHero.vue'
import PageHeader from '../components/common/PageHeader.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorState from '../components/common/ErrorState.vue'
import ResourceDetailModal from '../components/resources/ResourceDetailModal.vue'

const { accessToken, isLoggedIn } = useSession()

const items = ref<LearningRecordItem[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 10
const loading = ref(false)
const error = ref('')
const requestId = ref('')
const detailOpen = ref(false)
const detailId = ref<number | null>(null)
const detailProgress = ref<number | null>(null)
let sequence = 0

async function load(): Promise<void> {
  const seq = ++sequence
  if (!isLoggedIn.value) return
  loading.value = true; error.value = ''; requestId.value = ''
  try {
    const result = await listLearningRecords(page.value, pageSize)
    if (seq !== sequence) return
    total.value = result.total
    const last = Math.max(1, Math.ceil(total.value / pageSize))
    if (page.value > last) { page.value = last; return }
    items.value = result.items
  } catch (cause) {
    if (seq !== sequence) return
    items.value = []; total.value = 0
    if (cause instanceof ApiError && cause.status === 401) clearSession()
    else {
      error.value = cause instanceof Error ? cause.message : '学习进度加载失败'
      requestId.value = cause instanceof ApiError ? cause.requestId : ''
    }
  } finally { if (seq === sequence) loading.value = false }
}

/** 打开详情弹窗调整进度；已有进度作为滑块初始值。 */
function openAdjust(item: LearningRecordItem): void {
  detailId.value = item.resource_id
  detailProgress.value = item.progress
  detailOpen.value = true
}

function formatTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无记录'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(date)
}

watch(page, () => { void load() })
watch(accessToken, () => {
  sequence++; items.value = []; total.value = 0; loading.value = false; error.value = ''
  detailOpen.value = false; detailId.value = null; detailProgress.value = null
  if (isLoggedIn.value) { if (page.value !== 1) page.value = 1; else void load() }
}, { immediate: true, flush: 'sync' })
onUnmounted(() => { sequence++ })
</script>

<template>
  <StudentLayout>
    <PageHero>
      <PageHeader eyebrow="My Learning" title="学习进度" description="记录你看到哪儿了，下次从这里接着学。" />
    </PageHero>

    <UCard v-if="!isLoggedIn">
      <EmptyState centered title="登录后查看学习进度" description="进度只对当前账号可见。" />
      <div class="mt-5 flex justify-center">
        <UButton :to="{ path: '/login', query: { redirect: '/learning' } }">前往登录</UButton>
      </div>
    </UCard>

    <ErrorState v-else-if="error" :description="error" :request-id="requestId" @retry="load" />

    <template v-else>
      <p v-if="isLoggedIn && !loading" class="learning-total">
        共 <strong>{{ total }}</strong> 份资源有学习记录 · 最近学习在前
      </p>

      <div v-if="loading || items.length" class="learning-list" :aria-busy="loading">
        <div v-for="item in items" :key="item.id" class="learning-row"
          :class="{ 'learning-row--offline': !item.resource.is_available }">
          <div class="learning-row__main">
            <div class="learning-row__title-line">
              <span class="learning-row__title">{{ item.resource.title }}</span>
              <UBadge v-if="!item.resource.is_available" color="neutral" variant="subtle" size="sm">
                已下架
              </UBadge>
            </div>
            <p class="learning-row__meta">
              <span>{{ item.resource.course_title }}</span>
              <span aria-hidden="true">·</span>
              <span>{{ item.resource.category_name }}</span>
              <span aria-hidden="true">·</span>
              <span>最近学习 {{ formatTime(item.last_accessed_at) }}</span>
            </p>
          </div>

          <div class="learning-row__progress" :aria-label="`当前进度 ${item.progress}%`">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: `${item.progress}%` }" />
            </div>
            <span class="progress-value">{{ item.progress }}%</span>
          </div>

          <div class="learning-row__actions">
            <UButton
              v-if="item.resource.is_available"
              size="sm"
              color="primary"
              @click="openAdjust(item)"
            >
              查看资源详情
            </UButton>
            <span v-else class="learning-row__offline-hint">资源已下架，无法查看详情</span>
          </div>
        </div>
      </div>

      <UCard v-else>
        <EmptyState centered icon="i-lucide-book-open-check" title="还没有学习记录"
          description="在资源详情里拖动进度条并记录，这里就会出现你的进度。" />
        <div class="mt-5 flex justify-center">
          <UButton to="/resources">去资源中心</UButton>
        </div>
      </UCard>

      <div v-if="total > pageSize" class="mt-6 flex justify-center">
        <UPagination v-model:page="page" :total="total" :items-per-page="pageSize" :disabled="loading" />
      </div>
    </template>

    <ResourceDetailModal v-model:open="detailOpen" :resource-id="detailId" :initial-progress="detailProgress"
      @saved="load" />
  </StudentLayout>
</template>

<style scoped>
.learning-total {
  margin: 4px 0 16px;
  color: var(--lh-text-secondary);
  font-size: 13px;
}

.learning-total strong {
  color: var(--lh-primary);
}

.learning-list {
  display: grid;
  gap: 12px;
}

.learning-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(180px, 240px) auto;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  border: 1px solid var(--lh-border);
  border-radius: 12px;
  background: var(--lh-surface);
}

.learning-row--offline {
  background: var(--lh-surface-subtle, #f6f7f9);
}

.learning-row__main {
  min-width: 0;
}

.learning-row__title-line {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.learning-row__title {
  overflow: hidden;
  color: var(--lh-text);
  font-size: 15px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.learning-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 6px 0 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.learning-row__progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-track {
  flex: 1;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--lh-border);
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--lh-primary);
}

.learning-row--offline .progress-fill {
  background: var(--lh-text-secondary);
}

.progress-value {
  min-width: 40px;
  color: var(--lh-text);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.learning-row__actions {
  display: flex;
  justify-content: flex-end;
}

.learning-row__offline-hint {
  color: var(--lh-text-secondary);
  font-size: 12px;
}

@media (max-width: 767px) {
  .learning-row {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
    padding: 14px 16px;
  }

  .learning-row__actions {
    justify-content: flex-start;
  }
}
</style>
