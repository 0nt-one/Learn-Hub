import { request } from './client'
import type { Page } from '../types/api'

export interface Notification {
  id: number
  user_id: number
  review_record_id: number | null
  /** 审核类通知关联的资源；后端补上后，通知才能跳到审核历史 */
  resource_id?: number | null
  resource_title?: string | null
  kind: string
  title: string
  content: string
  read_at: string | null
  created_at: string
}

export function listNotifications(params: { page?: number; page_size?: number; unread_only?: boolean } = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) query.set(key, String(value))
  }
  return request<Page<Notification>>(`/users/me/notifications?${query}`)
}

export function markNotificationRead(id: number) {
  return request<Notification>(`/users/me/notifications/${id}/read`, { method: 'PATCH' })
}
