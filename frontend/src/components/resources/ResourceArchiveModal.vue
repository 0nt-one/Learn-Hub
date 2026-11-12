<script setup lang="ts">
import { computed, onUnmounted, ref, useId, watch } from 'vue'
import { archiveResource } from '../../api/resources'
import { ApiError } from '../../api/client'
import { clearSession, useSession } from '../../api/session'
import type { Resource } from '../../types/resource'

const open = defineModel<boolean>('open', { default: false })
const props = defineProps<{ resource: Resource | null }>()
const emit = defineEmits<{ archived: [resource: Resource]; refresh: [] }>()
const { accessToken, currentUser } = useSession()
const toast = useToast()
const id = useId()
const reason = ref('')
const error = ref('')
const busy = ref(false)
const stale = ref(false)
let active = true
const allowed = computed(() => props.resource && props.resource.status !== 'archived' && (
  currentUser.value?.role === 'admin' || (
    props.resource.owner_id === currentUser.value?.id && props.resource.status !== 'pending'
  )
))
watch([open, () => props.resource?.id], () => {
  // 关闭时不清空，避免退出动画里输入框内容突然消失
  if (!open.value) return
  reason.value = ''; error.value = ''; stale.value = false
})
watch(accessToken, () => { open.value = false; reason.value = ''; error.value = ''; busy.value = false }, { flush: 'sync' })
onUnmounted(() => { active = false })

async function confirm() {
  const resource = props.resource
  if (!resource || busy.value || stale.value) return
  if (!allowed.value) { error.value = '当前资源不能归档，待审核资源请先撤回。'; return }
  const text = reason.value.trim()
  if (!text || Array.from(text).length > 2000) { error.value = '请填写 1–2000 字的归档原因，不能只填空格。'; return }
  const token = accessToken.value
  busy.value = true
  error.value = ''
  try {
    const result = await archiveResource(resource.id, resource.version_id, text)
    if (!active || token !== accessToken.value) return
    open.value = false
    toast.add({ title: '资源已归档', description: '资源与审核历史已保留，不能再修改或提交审核。', color: 'success' })
    emit('archived', result)
  } catch (cause) {
    if (!active || token !== accessToken.value) return
    if (cause instanceof ApiError && cause.status === 401) { clearSession(); return }
    stale.value = cause instanceof ApiError && [403, 404, 409].includes(cause.status)
    error.value = cause instanceof ApiError
      ? cause.code === 'VERSION_CONFLICT' ? '资源已变化，请刷新列表后重新确认归档。'
        : cause.code === 'INVALID_STATE' ? '资源已归档，请刷新列表。'
          : cause.message
      : '归档失败，请稍后重试。'
  } finally { if (active && token === accessToken.value) busy.value = false }
}
function refresh() { open.value = false; emit('refresh') }
</script>

<template>
  <UModal v-model:open="open" title="归档资源" :description="resource?.title" :dismissible="!busy" :close="!busy"
    :ui="{ description: 'whitespace-normal break-words', footer: 'justify-end gap-3' }">
    <template #body>
      <div class="archive-form">
        <UAlert color="warning" variant="soft" icon="i-lucide-archive" title="归档后无法恢复"
          :description="resource?.status === 'pending' ? '该资源将退出待审队列，不能再修改、发布或提交审核。已有审核历史会保留。' : '资源将退出公开目录，不能再修改、发布或提交审核。已有审核历史会保留。'" />
        <div>
          <label :for="id" class="archive-form__label">归档原因 <span aria-hidden="true">*</span></label>
          <UTextarea :id="id" v-model="reason" required :rows="4" :maxlength="2000" :disabled="busy || stale" class="w-full"
            placeholder="请说明归档原因，例如：内容已过时，已发布替代资源。" :aria-describedby="`${id}-hint`" />
          <p :id="`${id}-hint`" class="archive-form__hint">原因将记录到操作日志中 · {{ Array.from(reason).length }}/2000</p>
        </div>
        <UAlert v-if="error" color="error" variant="soft" :title="error" />
      </div>
    </template>
    <template #footer>
      <UButton color="neutral" variant="outline" :disabled="busy" @click="open = false">取消</UButton>
      <UButton v-if="stale" @click="refresh">刷新列表</UButton>
      <UButton v-else color="error" :loading="busy" :disabled="!allowed" @click="confirm">确认归档</UButton>
    </template>
  </UModal>
</template>

<style scoped>
.archive-form { display: grid; gap: 20px; }
.archive-form__label { display: block; margin-bottom: 8px; font-size: 14px; font-weight: 600; }
.archive-form__label span { color: var(--lh-danger); }
.archive-form__hint { margin: 6px 0 0; font-size: 12px; color: var(--lh-text-secondary); }
</style>
