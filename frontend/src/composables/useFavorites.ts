import { reactive, ref, watch } from 'vue'
import { addFavorite, removeFavorite } from '../api/favorites'
import { clearSession, useSession } from '../api/session'
import { ApiError } from '../api/client'
const states = reactive(new Map<number, boolean>())
const pending = reactive(new Set<number>())
const revision = ref(0)
const { accessToken } = useSession()
let generation = 0
watch(accessToken, () => { generation++; states.clear(); pending.clear(); revision.value++ }, { flush: 'sync' })
export function useFavorites() {
  async function toggle(id: number, fallback: boolean) {
    if (pending.has(id)) return
    if (!accessToken.value) throw new Error('请先登录后收藏资源。')
    const current = generation
    const next = !(states.get(id) ?? fallback)
    pending.add(id)
    try {
      if (next) await addFavorite(id)
      else await removeFavorite(id)
      if (current !== generation) return
      states.set(id, next)
      revision.value++
    } catch (cause) {
      if (current !== generation) return
      if (cause instanceof ApiError && cause.status === 401) clearSession()
      throw cause
    } finally { if (current === generation) pending.delete(id) }
  }
  return { value: (id: number, fallback: boolean) => states.get(id) ?? fallback, pending, revision, toggle }
}
