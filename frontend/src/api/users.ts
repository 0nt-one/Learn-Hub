import { request } from './client'
import type { Page } from '../types/api'
import type { User, UserRole, UserUpdatePayload } from '../types/user'

/** GET /users/me —— 用当前令牌换取用户资料，也用于校验会话是否仍有效。 */
export function getMe(): Promise<User> {
  return request<User>('/users/me')
}

export interface UserListParams {
  page?: number
  page_size?: number
  /** null / undefined 表示不筛选 */
  role?: UserRole | null
  is_active?: boolean | null
  /** 用户名关键词，1–100 字符 */
  q?: string
}

/** GET /users —— 管理员分页查询用户，按 id 倒序。 */
export function listUsers(params: UserListParams = {}): Promise<Page<User>> {
  const query = new URLSearchParams()

  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.page_size !== undefined) query.set('page_size', String(params.page_size))
  if (params.role) query.set('role', params.role)
  if (params.is_active !== undefined && params.is_active !== null) {
    query.set('is_active', String(params.is_active))
  }
  if (params.q) query.set('q', params.q)

  const suffix = query.toString()
  return request<Page<User>>(`/users${suffix ? `?${suffix}` : ''}`)
}

/**
 * PATCH /users/{id} —— 管理员修改角色或启停账户。
 * 至少提交一个字段且不接受 null；改自己会返回 409 ADMIN_SELF_CHANGE_FORBIDDEN。
 */
export function updateUser(id: number, payload: UserUpdatePayload): Promise<User> {
  return request<User>(`/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
