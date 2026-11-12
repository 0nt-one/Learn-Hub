import { request } from './client'
import type { Page } from '../types/api'

export interface OperationLog {
  id: number
  actor_id: number
  action: string
  target_type: string
  target_id: number
  request_id: string
  summary: string
  created_at: string
}

export function listOperationLogs(page: number, filters: Record<string, string>, pageSize = 20) {
  const query = new URLSearchParams({ page: String(page), page_size: String(pageSize), ...filters })
  return request<Page<OperationLog>>('/operation-logs?' + query)
}
