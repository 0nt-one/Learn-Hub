<script setup lang="ts">
import { computed } from 'vue'
import FavoriteButton from './FavoriteButton.vue'
import type { ResourceSummary, ResourceType } from '../../types/resource'

/*
 * 资源卡片：轻量类型图标、标题摘要与课程信息，整卡打开详情。
 * loading=true 时用同一套骨架占位，接入接口前也可以用来核对布局密度。
 */
const props = withDefaults(
  defineProps<{
    resource?: ResourceSummary
    loading?: boolean
    /** 刷新期间禁用旧结果的打开动作；数据请求由页面负责。 */
    actionsDisabled?: boolean
    view?: 'grid' | 'list'
  }>(),
  { loading: false, actionsDisabled: true },
)

const emit = defineEmits<{ open: [] }>()

const COVER_ICON: Record<ResourceType, string> = {
  document: 'i-lucide-file-text',
  video: 'i-lucide-video',
  link: 'i-lucide-link-2',
}

const coverIcon = computed(() =>
  props.resource ? COVER_ICON[props.resource.resourceType] : 'i-lucide-file-text',
)

const updatedLabel = computed(() => {
  const raw = props.resource?.updatedAt
  if (!raw) return null
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return null
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
})
</script>

<template>
  <UCard :ui="{ root: 'min-w-0 overflow-hidden rounded-2xl shadow-sm', body: 'p-0 sm:p-0 h-full' }">
    <div v-if="loading" class="card card--loading" :class="{ 'card--list': view === 'list' }">
      <div class="card__cover card__cover--placeholder" aria-hidden="true">
        <UIcon name="i-lucide-image" class="card__cover-icon" />
      </div>
      <div class="card__body">
        <div class="card__badges" aria-hidden="true">
          <USkeleton class="h-5 w-14" />
          <USkeleton class="h-5 w-16" />
        </div>
        <USkeleton class="h-4 w-full" />
        <USkeleton class="h-4 w-3/4" />
        <USkeleton class="h-3 w-full" />
        <USkeleton class="h-3 w-2/3" />
        <div class="card__footer" aria-hidden="true">
          <USkeleton class="h-3 w-20" />
        </div>
      </div>
      <span class="sr-only">正在加载资源</span>
    </div>

    <div v-else-if="resource" class="card" :class="[{ 'card--list': view === 'list', 'card--interactive': !actionsDisabled }, `card--${resource.resourceType}`]"
      >
      <button class="card__open" data-resource-card type="button" :disabled="actionsDisabled" :aria-disabled="actionsDisabled"
        :aria-label="`查看资源详情：${resource.title}`" @click="emit('open')"></button>
      <FavoriteButton v-if="resource.isFavorited !== undefined" class="card__favorite" compact :resource-id="resource.id" :favorited="resource.isFavorited" :disabled="actionsDisabled" />
      <div class="card__geometry" aria-hidden="true"></div>
      <div class="card__type">
      <div class="card__cover" :class="`card__cover--${resource.resourceType}`" aria-hidden="true">
        <UIcon :name="coverIcon" class="card__cover-icon" />
      </div>
      <span>{{ { document: '文档', video: '视频', link: '链接' }[resource.resourceType] }}</span>
      </div>

      <div class="card__body">
        <div class="card__badges">
          <span v-if="resource.categoryName" class="card__category" :title="resource.categoryName">{{ resource.categoryName }}</span>
        </div>

        <h3 class="card__title line-clamp-2" :title="resource.title">{{ resource.title }}</h3>
        <p class="card__description line-clamp-2">
          {{ resource.description || '暂无资源说明' }}
        </p>
        <p v-if="resource.courseName" class="card__course" :title="resource.courseName"><UIcon name="i-lucide-book-open" class="shrink-0" /><span>{{ resource.courseName }}</span></p>

        <div class="card__footer">
          <p v-if="updatedLabel" class="card__meta">更新于 {{ updatedLabel }}</p>
          <p v-else class="card__meta">时间未知</p>

          <span class="card__arrow-wrap" aria-hidden="true"><UIcon name="i-lucide-arrow-right" class="card__arrow" /></span>
        </div>
      </div>
    </div>
  </UCard>
</template>

<style scoped>
.card.card--list { flex-direction: row; align-items: flex-start; }
.card--list .card__cover { width: 64px; height: 64px; flex: none; }
.card__title { overflow-wrap: anywhere; }
.card__badges { overflow-wrap: anywhere; }
.card__footer { flex-wrap: wrap; }
.card {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 18px;
  gap: 12px;
  border-radius: 16px;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  transition: box-shadow .18s ease;
}
.card--interactive { cursor: pointer; background: var(--lh-surface); }
.card--interactive:hover { box-shadow: inset 0 0 0 1px var(--lh-primary-border); }
.card--interactive:hover .card__title, .card--interactive:hover .card__arrow { color: var(--lh-primary); }
.card--interactive:focus-visible { outline: 2px solid var(--lh-primary); outline-offset: -3px; background: var(--lh-primary-soft); }

.card__cover {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  color: var(--lh-primary);
}

.card__cover--document {
  background: var(--lh-primary-soft);
}

.card__cover--video {
  background: #f0edff;
  color: #6d5bd0;
}

.card__cover--link {
  background: #eaf7f2;
  color: #21856a;
}

.card__cover--placeholder {
  background: var(--lh-surface-subtle);
  color: var(--lh-text-dimmed);
}

.card__cover-icon {
  width: 20px;
  height: 20px;
}

.card__body {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  padding: 0;
}

.card--loading .card__body {
  min-width: 0;
  gap: 10px;
}

.card__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.card__category { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; font-size: 12px; color: var(--lh-text-secondary); }
.card__course { display: flex; align-items: center; gap: 6px; margin: 4px 0 0; font-size: 12px; color: var(--lh-text-secondary); }
.card__course span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card__arrow { width: 16px; height: 16px; color: var(--lh-text-secondary); }
.card:not(.card--list) .card__description { min-height: 40px; }
.card--list .card__description { -webkit-line-clamp: 1; }
@media (max-width: 479px) {
  .card { padding: 16px; gap: 12px; }
  .card--list .card__cover { width: 40px; height: 40px; }
}

.card__title {
  margin: 0;
  color: var(--lh-text);
  font-size: 20px;
  font-weight: 700;
  line-height: 28px;
}

.card__description {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 0;
}

.card__meta {
  margin: 0;
  color: var(--lh-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.card__type { display: flex; align-items: center; gap: 14px; font-size: 13px; color: var(--lh-text-secondary); }
.card__type, .card__body { position: relative; z-index: 1; }
.card__type, .card__body { pointer-events: none; }
.card__open { position: absolute; inset: 0; z-index: 2; cursor: pointer; border-radius: inherit; }
.card__open:focus-visible { outline: 2px solid var(--lh-primary); outline-offset: -3px; }
.card__open:disabled { cursor: default; }
.card__favorite { position: absolute; top: 14px; right: 14px; z-index: 3; }
.card__type { padding-right: 40px; }
.card--list .card__footer { padding-top: 38px; }
.card__geometry { position: absolute; top: -34px; right: -30px; width: 144px; height: 120px; z-index: 0; pointer-events: none; opacity: .55; }
.card--link .card__geometry { border: 32px solid #c6eee4; border-radius: 50%; transform: rotate(-25deg); }
.card--video .card__geometry { background: #e1dcfa; clip-path: polygon(35% 0, 100% 0, 100% 100%, 0 40%); transform: rotate(12deg); }
.card--document .card__geometry { border: 1px solid #bfd3fa; background: #eaf0ff; border-radius: 24px; transform: rotate(-30deg); }
.card--document .card__geometry::after { content: ''; position: absolute; inset: 20px; border: 1px solid #bfd3fa; border-radius: 16px; }
.card__arrow-wrap { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; background: var(--lh-primary-soft); color: var(--lh-primary); flex: none; }
.card__arrow { color: inherit; transition: transform .18s ease; }
.card--interactive:hover .card__arrow { transform: translateX(2px); }
.card__body { gap: 8px; }
.card:not(.card--list) { min-height: 250px; }
.card.card--list .card__type { flex-direction: column; gap: 8px; flex: none; }
.card--list .card__geometry { width: 120px; height: 100px; opacity: .3; }
.card.card--list { padding: 14px 18px; gap: 16px; }
.card--list .card__cover { width: 40px; height: 40px; }
.card--list .card__title { font-size: 18px; line-height: 26px; -webkit-line-clamp: 1; }
.card--list .card__body { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 20px; }
.card--list .card__badges, .card--list .card__title, .card--list .card__description, .card--list .card__course { grid-column: 1; }
/* 列表视图的右列从卡片顶部开始，要给收藏按钮留出高度，否则"更新于…"会被按钮压住 */
.card--list .card__footer { grid-column: 2; grid-row: 1 / 5; flex-direction: column; justify-content: space-between; align-items: flex-end; margin: 0; padding: 44px 0 0; }
.card--list .card__course { margin-top: 2px; }
@media (max-width: 479px) {
  .card { padding: 18px; }
  .card__title { font-size: 20px; line-height: 28px; }
  .card:not(.card--list) { min-height: 250px; }
  .card--list .card__body { grid-template-columns: minmax(0, 1fr); }
  .card--list .card__footer { grid-column: 1; grid-row: auto; flex-direction: row; align-items: center; padding: 0; }
}
@media (prefers-reduced-motion: reduce) { .card, .card__arrow { transition: none; } .card--interactive:hover .card__arrow { transform: none; } }

</style>


