import { onUnmounted, ref, shallowRef } from 'vue'
import type { Page } from '../types/api'
import { ApiError } from '../api/client'

/** 每次按需加载一页，避免把字典第一页误当成全部数据。 */
export function usePagedOptions<T extends { id: number }>(
  loader: (page: number) => Promise<Page<T>>,
  onUnauthorized: () => void,
) {
  const items = shallowRef<T[]>([])
  const loading = ref(false)
  const error = ref('')
  const more = ref(true)
  let page = 1
  let generation = 0

  function reset() {
    generation++
    items.value = []
    page = 1
    more.value = true
    error.value = ''
    loading.value = false
  }

  async function loadMore() {
    if (loading.value || !more.value) return
    const requestGeneration = generation
    loading.value = true
    error.value = ''
    try {
      const result = await loader(page)
      if (requestGeneration !== generation) return
      items.value = [...new Map([...items.value, ...result.items].map(item => [item.id, item])).values()]
      more.value = page * result.page_size < result.total
      page++
    } catch (cause) {
      if (requestGeneration !== generation) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else error.value = cause instanceof ApiError ? cause.message : '加载失败，请重试。'
    } finally {
      if (requestGeneration === generation) loading.value = false
    }
  }

  onUnmounted(reset)
  return { items, loading, error, more, reset, loadMore }
}
