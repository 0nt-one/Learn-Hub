import { request } from './client'
import type { LearningRecord, LearningRecordPage } from '../types/learning'

/** GET /users/me/learning-records —— 我的学习进度，最近学习在前。 */
export function listLearningRecords(page = 1, pageSize = 20): Promise<LearningRecordPage> {
  return request<LearningRecordPage>(
    `/users/me/learning-records?page=${page}&page_size=${pageSize}`,
  )
}

/**
 * PUT /users/me/learning-records/{id} —— 记录某个资源的进度。
 * 没有记录则创建，已存在则覆盖（后端做安全 upsert，重复请求不会产生两条）。
 */
export function recordLearningProgress(resourceId: number, progress: number): Promise<LearningRecord> {
  return request<LearningRecord>(`/users/me/learning-records/${resourceId}`, {
    method: 'PUT',
    body: JSON.stringify({ progress }),
  })
}
