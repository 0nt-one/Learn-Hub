import { request } from './client'
import type { Page } from '../types/api'
import type { Category, CategoryCreatePayload, CategoryUpdatePayload } from '../types/category'

export interface CategoryListParams {
  page?: number
  page_size?: number
  /** null / undefined 表示不筛选；非管理员查停用分类会 403 */
  is_active?: boolean | null
}

/** GET /categories —— 分页查询，名称升序。 */
export function listCategories(params: CategoryListParams = {}): Promise<Page<Category>> {
  const query = new URLSearchParams()

  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.page_size !== undefined) query.set('page_size', String(params.page_size))
  if (params.is_active !== undefined && params.is_active !== null) {
    query.set('is_active', String(params.is_active))
  }

  const suffix = query.toString()
  return request<Page<Category>>(`/categories${suffix ? `?${suffix}` : ''}`)
}

/** POST /categories —— 管理员新建，名称重复返回 409 CATEGORY_NAME_EXISTS。 */
export function createCategory(payload: CategoryCreatePayload): Promise<Category> {
  return request<Category>('/categories', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** PATCH /categories/{id} —— 至少提交一个字段，改名称同样受唯一约束。 */
export function updateCategory(id: number, payload: CategoryUpdatePayload): Promise<Category> {
  return request<Category>(`/categories/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
