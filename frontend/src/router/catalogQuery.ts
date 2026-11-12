import type { LocationQuery, LocationQueryRaw } from 'vue-router'
import type { ResourceListParams } from '../api/resources'

function positiveId(value: unknown): number | undefined {
  if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value)) return undefined
  const parsed = Number(value)
  return Number.isSafeInteger(parsed) ? parsed : undefined
}

/** URL 是目录筛选的唯一来源；未知枚举、数组和非法数字回到默认值。 */
export function parseCatalogQuery(query: LocationQuery): ResourceListParams {
  const q = typeof query.q === 'string' ? query.q.trim().slice(0, 100) : ''
  const type = query.resource_type
  return {
    q: q || undefined,
    course_id: positiveId(query.course_id),
    category_id: positiveId(query.category_id),
    resource_type: type === 'document' || type === 'video' || type === 'link' ? type : undefined,
    sort: query.sort === 'title' ? 'title' : 'newest',
    page: positiveId(query.page) ?? 1,
    page_size: query.page_size === '40' ? 40 : 20,
  }
}

export function catalogQuery(params: ResourceListParams): LocationQueryRaw {
  const query: LocationQueryRaw = {}
  if (params.q) query.q = params.q
  if (params.course_id) query.course_id = String(params.course_id)
  if (params.category_id) query.category_id = String(params.category_id)
  if (params.resource_type) query.resource_type = params.resource_type
  if (params.sort === 'title') query.sort = params.sort
  if (params.page && params.page > 1) query.page = String(params.page)
  if (params.page_size === 40) query.page_size = '40'
  return query
}
