<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { getResource } from '../../api/resources'
import { recordLearningProgress } from '../../api/learning'
import { ApiError } from '../../api/client'
import { clearSession, useSession } from '../../api/session'
import type { Resource } from '../../types/resource'
import ErrorState from '../common/ErrorState.vue'
import ResourceTypeBadge from './ResourceTypeBadge.vue'
import FavoriteButton from './FavoriteButton.vue'
const detailOpen = defineModel<boolean>('open', { default: false })
const props = defineProps<{ resourceId: number | null; initialProgress?: number | null }>()
const emit = defineEmits<{ saved: [resourceId: number, progress: number] }>()
const detailId = computed(() => props.resourceId)
const selected = ref<Resource | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const detailRequestId = ref('')
let detailSequence = 0
const { accessToken, isLoggedIn } = useSession()
const draftProgress = ref(0)
const savingProgress = ref(false)
const progressMessage = ref('')
function expireSession() { clearSession() }
watch([detailOpen, detailId], () => {
  detailSequence++
  /*
   * 只在打开时重置内容。关闭时若立刻把 selected 置空，退出动画会缩成一个
   * 只剩标题和说明的空白弹窗，看起来像"闪了一下另一个弹窗"。
   */
  if (!detailOpen.value) return
  selected.value = null
  detailLoading.value = false
  draftProgress.value = props.initialProgress ?? 0; progressMessage.value = ''
  void loadDetail()
}, { flush: 'sync', immediate: true })
watch(accessToken, () => { detailSequence++; detailOpen.value = false; selected.value = null }, { flush: 'sync' })
onUnmounted(() => { detailSequence++ })
async function loadDetail() {
  if (detailId.value === null || !detailOpen.value) return
  const current = ++detailSequence
  selected.value = null
  detailLoading.value = true
  detailError.value = ''
  detailRequestId.value = ''
  try {
    const resource = await getResource(detailId.value)
    if (current === detailSequence && detailOpen.value) selected.value = resource
  } catch (cause) {
    if (current !== detailSequence) return
    if (cause instanceof ApiError && cause.status === 401) expireSession()
    else {
      detailError.value = cause instanceof ApiError
        ? cause.status === 404 ? '资源不存在或暂不可用。' : cause.message
        : '资源详情加载失败，请重试。'
      detailRequestId.value = cause instanceof ApiError ? cause.requestId : ''
    }
  } finally {
    if (current === detailSequence) detailLoading.value = false
  }
}
const externalUrl = computed(() => {
  if (!selected.value) return null
  try {
    const url = new URL(selected.value.url)
    return url.protocol === 'https:' && !url.username && !url.password ? url : null
  } catch { return null }
})
const detailUpdatedAt = computed(() => {
  if (!selected.value) return ''
  const date = new Date(selected.value.updated_at)
  return Number.isNaN(date.getTime()) ? '暂无记录' : new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(date)
})

/** 拖动时只改本地值，点「记录」才发请求，避免每动一格打一次接口。 */
function onSlide(event: Event): void {
  const target = event.target as HTMLInputElement
  draftProgress.value = Number(target.value)
}

async function saveProgress(): Promise<void> {
  if (!selected.value || savingProgress.value) return
  savingProgress.value = true
  progressMessage.value = ''
  try {
    await recordLearningProgress(selected.value.id, draftProgress.value)
    progressMessage.value = `已记录 ${draftProgress.value}%`
    emit('saved', selected.value.id, draftProgress.value)
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 401) { expireSession(); return }
    progressMessage.value = cause instanceof Error ? cause.message : '记录失败，请重试。'
  } finally {
    savingProgress.value = false
  }
}

</script>
<template>
    <UModal v-model:open="detailOpen" :title="selected?.title ?? '资源详情'" description="了解资源内容，开始你的学习。"
      :ui="{ content: 'sm:max-w-2xl', title: 'text-xl font-semibold leading-snug break-words', description: 'mt-2 text-sm text-muted', body: 'p-5 sm:p-6', footer: 'justify-end gap-3 bg-muted/30' }">
      <template #body>
        <div v-if="detailLoading" class="space-y-4" role="status" aria-busy="true">
          <span class="sr-only">正在加载资源详情</span>
          <USkeleton class="h-6 w-1/3" />
          <USkeleton class="h-24 w-full" />
        </div>
        <ErrorState v-else-if="detailError" :description="detailError" :request-id="detailRequestId"
          @retry="loadDetail" />
        <div v-else-if="selected" class="resource-info">
          <section class="resource-info__section" aria-label="基本信息">
            <div class="resource-info__heading">
              <h3>基本信息</h3>
              <ResourceTypeBadge :type="selected.resource_type" />
            </div>
            <dl class="resource-info__metadata">
              <div>
                <dt>所属课程</dt>
                <dd>{{ selected.course_title || '暂无课程' }}</dd>
              </div>
              <div>
                <dt>课程负责人</dt>
                <dd>{{ selected.course_teacher_display_name }}</dd>
              </div>
              <div>
                <dt>资源分类</dt>
                <dd>{{ selected.category_name || '暂无分类' }}</dd>
              </div>
              <div>
                <dt>资源投稿者</dt>
                <dd>{{ selected.owner_display_name }}</dd>
              </div>
              <div v-if="selected.page_count">
                <dt>文档页数</dt>
                <dd>{{ selected.page_count }} 页</dd>
              </div>
              <div v-if="selected.duration_seconds">
                <dt>视频时长</dt>
                <dd>{{ Math.ceil(selected.duration_seconds / 60) }} 分钟</dd>
              </div>
              <div>
                <dt>更新时间（本地）</dt>
                <dd>{{ detailUpdatedAt }}</dd>
              </div>
            </dl>
          </section>
          <section class="resource-info__section" aria-label="资源说明">
            <h3>资源说明</h3>
            <p class="resource-info__description">{{ selected.description || '暂无资源说明。' }}</p>
          </section>
          <section v-if="isLoggedIn" class="resource-info__section" aria-label="学习进度">
            <h3>记录学习进度</h3>
            <div class="progress-slider">
              <input
                class="progress-slider__input"
                type="range"
                min="0"
                max="100"
                step="1"
                :value="draftProgress"
                :disabled="savingProgress"
                aria-label="学习进度百分比"
                @input="onSlide"
              />
              <output class="progress-slider__value">{{ draftProgress }}%</output>
              <UButton size="sm" :loading="savingProgress" @click="saveProgress">记录</UButton>
            </div>
            <p class="progress-hint" role="status">
              {{ progressMessage || '拖动到你的位置后点「记录」，进度只对你自己可见。' }}
            </p>
          </section>
          <div class="resource-info__source">
            <UIcon name="i-lucide-external-link" class="resource-info__source-icon" />
            <div><span class="resource-info__source-label">资源来源</span>
              <p class="resource-info__domain">{{ externalUrl?.hostname ?? '资源地址不可用' }}</p>
              <p v-if="externalUrl" class="resource-info__hint">点击下方按钮，在新窗口查看完整内容。</p>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <FavoriteButton v-if="selected" :resource-id="selected.id" :favorited="selected.is_favorited" />
        <UButton color="neutral" variant="outline" @click="detailOpen = false">关闭</UButton>
        <UButton v-if="externalUrl" :to="externalUrl.href" target="_blank" rel="noopener noreferrer"
          trailing-icon="i-lucide-external-link">查看资源</UButton>
      </template>
    </UModal>
</template>
<style scoped>
.resource-info {
  display: grid;
  gap: 24px;
  font-size: 14px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.resource-info__section {
  display: grid;
  gap: 12px;
  min-width: 0;
}
.resource-info h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--lh-text);
}
.resource-info__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.resource-info__metadata {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 24px;
  margin: 0;
  padding: 18px 20px;
  border: 1px solid var(--lh-border);
  border-radius: 12px;
  background: var(--lh-surface-subtle);
}
.resource-info__metadata dt {
  margin-bottom: 4px;
  color: var(--lh-text-secondary);
  font-size: 12px;
}
.resource-info__metadata dd {
  margin: 0;
  font-weight: 500;
}
.resource-info__description {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.9;
}
.resource-info__source {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: var(--lh-primary-soft);
}
.resource-info__source-icon {
  flex: none;
  width: 20px;
  height: 20px;
  margin-top: 2px;
  color: var(--lh-primary);
}
.resource-info__source-label,
.resource-info__hint {
  font-size: 12px;
  color: var(--lh-text-secondary);
}
.resource-info__domain {
  margin: 2px 0 4px;
  font-weight: 600;
}
.resource-info__hint {
  margin: 0;
}
.resource-info__metadata {
    grid-template-columns: 1fr;
    gap: 14px;
    padding: 16px;
  }
@media(max-width:479px){.resource-info__metadata{grid-template-columns:1fr}}

.progress-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-slider__input {
  flex: 1;
  min-width: 0;
  accent-color: var(--lh-primary);
}

.progress-slider__value {
  min-width: 44px;
  color: var(--lh-text);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.progress-hint {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
}
</style>
