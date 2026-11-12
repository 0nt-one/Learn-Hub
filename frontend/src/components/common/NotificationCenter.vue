<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { listNotifications, markNotificationRead, type Notification } from '../../api/notifications'
import { ApiError } from '../../api/client'
import { clearSession, useSession } from '../../api/session'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'
import ReviewHistoryModal from '../resources/ReviewHistoryModal.vue'

const { accessToken } = useSession()
const open = ref(false)
const unreadOnly = ref(false)
const historyOpen = ref(false)
const historyResource = ref<{ id: number; title: string } | null>(null)
const unread = ref<number | null>(null)
const items = ref<Notification[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const error = ref('')
const requestId = ref('')
const actionError = ref('')
const saving = ref<number | null>(null)
let listSequence = 0
let countSequence = 0
let active = true

async function refreshCount() {
  const seq = ++countSequence
  const token = accessToken.value
  if (!token) return
  try {
    const result = await listNotifications({ page_size: 1, unread_only: true })
    if (active && seq === countSequence && token === accessToken.value) unread.value = result.total
  } catch (cause) {
    if (!active || seq !== countSequence || token !== accessToken.value) return
    unread.value = null
    if (cause instanceof ApiError && cause.status === 401) clearSession()
  }
}

async function load() {
  const seq = ++listSequence
  items.value = []
  error.value = ''
  requestId.value = ''
  if (!open.value || !accessToken.value) { loading.value = false; return }
  loading.value = true
  try {
    const result = await listNotifications({ page: page.value, page_size: pageSize, unread_only: unreadOnly.value })
    if (!active || seq !== listSequence) return
    total.value = result.total
    const lastPage = Math.max(1, Math.ceil(result.total / pageSize))
    if (page.value > lastPage) { page.value = lastPage; return }
    items.value = result.items
  } catch (cause) {
    if (!active || seq !== listSequence) return
    if (cause instanceof ApiError && cause.status === 401) { clearSession(); return }
    error.value = cause instanceof ApiError ? cause.message : '通知加载失败，请重试。'
    requestId.value = cause instanceof ApiError ? cause.requestId : ''
  } finally { if (seq === listSequence) loading.value = false }
}

async function markRead(item: Notification) {
  if (saving.value !== null || item.read_at) return
  const token = accessToken.value
  saving.value = item.id
  actionError.value = ''
  try {
    const updated = await markNotificationRead(item.id)
    if (!active || token !== accessToken.value) return
    items.value = items.value.map(row => row.id === updated.id ? updated : row)
    await refreshCount()
    if (active && token === accessToken.value && open.value && unreadOnly.value) await load()
  } catch (cause) {
    if (!active || token !== accessToken.value) return
    if (cause instanceof ApiError && cause.status === 401) clearSession()
    else actionError.value = cause instanceof ApiError ? cause.message : '标记失败，请重试。'
  } finally { if (active && token === accessToken.value) saving.value = null }
}

function refresh() { actionError.value = ''; void refreshCount(); void load() }

/** 只有审核类通知、并且后端给了 resource_id 时，才能跳到审核历史 */
function canOpenHistory(item: Notification): boolean {
  return item.kind === 'review_result' && typeof item.resource_id === 'number'
}

function openHistory(item: Notification): void {
  if (!canOpenHistory(item) || item.resource_id == null) return
  historyResource.value = { id: item.resource_id, title: item.resource_title ?? item.title }
  historyOpen.value = true
  if (!item.read_at) void markRead(item)
}
watch([open, unreadOnly], () => {
  listSequence++
  items.value = []
  total.value = 0
  actionError.value = ''
  if (page.value !== 1) page.value = 1
  else void load()
  if (open.value) void refreshCount()
}, { flush: 'sync' })
watch(page, () => { void load() })
watch(accessToken, () => {
  listSequence++; countSequence++
  open.value = false
  items.value = []; total.value = 0; unread.value = null; saving.value = null
  unreadOnly.value = false
  void refreshCount()
}, { immediate: true, flush: 'sync' })

function onFocus() { void refreshCount() }
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  window.addEventListener('focus', onFocus)
  timer = setInterval(() => { if (document.visibilityState === 'visible') void refreshCount() }, 60000)
})
onUnmounted(() => {
  active = false; listSequence++; countSequence++
  clearInterval(timer)
  window.removeEventListener('focus', onFocus)
})
function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '时间未知' : new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium', timeStyle: 'short', hour12: false,
  }).format(date)
}
</script>

<template>
  <div class="notification-trigger">
    <UButton color="neutral" variant="ghost" icon="i-lucide-bell" :aria-label="unread === null ? '打开通知' : `打开通知，${unread} 条未读`" :aria-expanded="open" @click="open = true" />
    <span v-if="unread && unread > 0" class="notification-trigger__count" aria-hidden="true">{{ unread > 99 ? '99+' : unread }}</span>
  </div>
  <USlideover v-model:open="open" title="通知" :ui="{ content: 'w-full sm:max-w-lg', footer: 'justify-between flex-wrap gap-3' }">
    <template #body>
      <div class="notifications">
        <div class="notifications__toolbar">
          <div class="notifications__filters" role="group" aria-label="通知筛选">
            <UButton :variant="unreadOnly ? 'ghost' : 'soft'" :aria-pressed="!unreadOnly" @click="unreadOnly = false">全部</UButton>
            <UButton :variant="unreadOnly ? 'soft' : 'ghost'" :aria-pressed="unreadOnly" @click="unreadOnly = true">未读{{ unread === null ? '' : ` (${unread})` }}</UButton>
          </div>
          <UButton color="neutral" variant="ghost" icon="i-lucide-refresh-cw" :loading="loading" aria-label="刷新通知" @click="refresh" />
        </div>
        <UAlert v-if="actionError" color="error" variant="soft" :title="actionError" />
        <div v-if="loading" class="space-y-4" role="status" aria-label="正在加载通知" aria-busy="true">
          <USkeleton v-for="n in 3" :key="n" class="h-32 w-full" />
        </div>
        <ErrorState v-else-if="error" :description="error" :request-id="requestId" @retry="refresh" />
        <EmptyState v-else-if="!items.length" centered icon="i-lucide-bell" :title="unreadOnly ? '没有未读通知' : '暂无通知'" description="有新消息时，会显示在这里。" />
        <ol v-else class="notifications__list">
          <li
            v-for="item in items"
            :key="item.id"
            class="notification"
            :class="{
              'notification--unread': !item.read_at,
              'notification--clickable': canOpenHistory(item),
            }"
            :tabindex="canOpenHistory(item) ? 0 : undefined"
            :role="canOpenHistory(item) ? 'button' : undefined"
            :aria-label="canOpenHistory(item) ? `查看「${item.resource_title ?? item.title}」的审核历史` : undefined"
            @click="openHistory(item)"
            @keydown.enter.prevent="openHistory(item)"
            @keydown.space.prevent="openHistory(item)"
          >
            <div class="notification__heading"><h3>{{ item.title }}</h3><UBadge :color="item.read_at ? 'neutral' : 'primary'" variant="soft" class="shrink-0">{{ item.read_at ? '已读' : '未读' }}</UBadge></div>
            <p class="notification__content">{{ item.content }}</p>
            <div class="notification__footer">
              <time :datetime="item.created_at">{{ formatDate(item.created_at) }}</time>
              <div class="notification__actions">
                <UButton v-if="canOpenHistory(item)" variant="link" size="sm" icon="i-lucide-history" @click.stop="openHistory(item)">审核历史</UButton>
                <UButton v-if="!item.read_at" variant="link" size="sm" :loading="saving === item.id" :disabled="saving !== null" @click.stop="markRead(item)">标记已读</UButton>
              </div>
            </div>
          </li>
        </ol>
      </div>
    </template>
    <template #footer>
      <span class="notifications__total">共 {{ total }} 条{{ unreadOnly ? '未读通知' : '通知' }}</span>
      <UPagination v-if="total > pageSize" v-model:page="page" :total="total" :items-per-page="pageSize" :sibling-count="0" :disabled="loading" size="sm" />
    </template>
  </USlideover>

  <ReviewHistoryModal v-model:open="historyOpen" :resource="historyResource" />
</template>

<style scoped>
.notification-trigger { position: relative; flex: none; }
.notification-trigger__count { position: absolute; top: -4px; right: -5px; min-width: 16px; padding: 0 4px; border-radius: 10px; background: var(--lh-danger); color: white; font-size: 10px; line-height: 16px; text-align: center; pointer-events: none; }
.notifications, .notifications__list { display: grid; gap: 16px; }
.notifications__list { list-style: none; padding: 0; margin: 0; }
.notifications__toolbar, .notification__heading, .notification__footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.notifications__filters { display: flex; gap: 4px; }
.notification { padding: 16px; border: 1px solid var(--lh-border); border-radius: 12px; min-width: 0; }
.notification--unread { background: var(--lh-primary-soft); }
.notification__heading { align-items: flex-start; }
.notification h3 { margin: 0; font-size: 14px; font-weight: 600; line-height: 1.6; overflow-wrap: anywhere; min-width: 0; }
.notification__content { margin: 12px 0; font-size: 14px; line-height: 1.8; white-space: pre-wrap; overflow-wrap: anywhere; }
.notification__footer { flex-wrap: wrap; }
.notification__actions { display: flex; align-items: center; gap: 4px; }
/* 可点击的通知：整卡可点进审核历史 */
.notification--clickable { cursor: pointer; }
.notification--clickable:hover { border-color: var(--lh-primary); }
.notification--clickable:focus-visible { outline: 2px solid var(--lh-primary); outline-offset: 2px; }
.notification time, .notifications__total { color: var(--lh-text-secondary); font-size: 12px; }
</style>
