import { request } from './client'
import type { Page } from '../types/api'
import type {
  Resource,
  ResourceCreatePayload,
  ResourceStatus,
  ResourceUpdatePayload,
  ResourceSort,
  ResourceType,
} from '../types/resource'

export interface ResourceListParams {
  q?: string
  course_id?: number
  category_id?: number
  resource_type?: ResourceType
  sort?: ResourceSort
  page?: number
  page_size?: number
}

export function getResource(id: number): Promise<Resource> {
  return request<Resource>(`/resources/${id}`)
}

/** 已授权的公开资源目录；课程和分类名称由响应提供。 */
export function listResources(params: ResourceListParams): Promise<Page<Resource>> {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  return request<Page<Resource>>(`/resources?${query}`)
}

export interface MyResourceListParams {
  page?: number
  page_size?: number
  /** null / undefined 表示不筛选 */
  status?: ResourceStatus | null
}

export function listAdminResources(params: ResourceListParams & { status?: ResourceStatus }): Promise<Page<Resource>> {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  return request<Page<Resource>>(`/resources/admin?${query}`)
}

/**
 * GET /resources/mine —— 当前登录用户自己创建的资源，按创建时间倒序。
 * 学生和教师都能调；返回里带所有状态（包括草稿）。
 */
export function listMyResources(params: MyResourceListParams = {}): Promise<Page<Resource>> {
  const query = new URLSearchParams()

  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.page_size !== undefined) query.set('page_size', String(params.page_size))
  if (params.status) query.set('status', params.status)

  const suffix = query.toString()
  return request<Page<Resource>>(`/resources/mine${suffix ? `?${suffix}` : ''}`)
}

/**
 * POST /resources —— 创建资源，成功后状态是 draft（草稿）。
 * 课程或分类停用会返回 409 REFERENCE_INACTIVE，元数据不符合类型会返回 422 VALIDATION_ERROR。
 */
export function createResource(payload: ResourceCreatePayload): Promise<Resource> {
  return request<Resource>('/resources', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * PATCH /resources/{id} —— 本人修改草稿或被驳回的资源。
 * 必须带 expected_version：版本不一致返回 409 VERSION_CONFLICT；
 * 状态不是 draft/rejected 返回 409 INVALID_STATE。
 */
export function updateResource(id: number, payload: ResourceUpdatePayload): Promise<Resource> {
  return request<Resource>(`/resources/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

/**
 * POST /resources/{id}/submit —— 把草稿或被驳回的资源送审。
 * 必须带 expected_version；状态不对返回 409 INVALID_STATE，版本过期返回 409 VERSION_CONFLICT。
 */
export function submitResource(id: number, expectedVersion: number): Promise<Resource> {
  return request<Resource>(`/resources/${id}/submit`, {
    method: 'POST',
    body: JSON.stringify({ expected_version: expectedVersion }),
  })
}

/** 本人撤回待审核或已发布资源，成功后回到草稿。 */
export function withdrawResource(id: number, expectedVersion: number): Promise<Resource> {
  return request<Resource>(`/resources/${id}/withdraw`, {
    method: 'POST',
    body: JSON.stringify({ expected_version: expectedVersion }),
  })
}

export function archiveResource(id: number, expectedVersion: number, reason: string): Promise<Resource> {
  return request<Resource>(`/resources/${id}/archive`, {
    method: 'POST',
    body: JSON.stringify({ expected_version: expectedVersion, reason }),
  })
}
