import { request } from './client'
import type { Page } from '../types/api'
import type { Resource } from '../types/resource'
import type { Review, ReviewCreatePayload, ReviewResult } from '../types/review'

export interface PendingReviewParams {
  page?: number
  page_size?: number
  /** 只看某门课程的待审资源 */
  course_id?: number
}

/**
 * GET /reviews/pending —— 待审队列，按提交时间升序（先提交的先审）。
 * 教师只能看到自己负责课程下的资源，管理员看全部；自己的投稿不会出现在自己的队列里。
 */
export function listPendingReviews(params: PendingReviewParams = {}): Promise<Page<Resource>> {
  const query = new URLSearchParams()

  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.page_size !== undefined) query.set('page_size', String(params.page_size))
  if (params.course_id !== undefined) query.set('course_id', String(params.course_id))

  const suffix = query.toString()
  return request<Page<Resource>>(`/reviews/pending${suffix ? `?${suffix}` : ''}`)
}

/**
 * POST /resources/{id}/reviews —— 作出审核决定。
 * 不能审自己的资源（403 SELF_REVIEW_FORBIDDEN）；资源必须处于 pending；
 * expected_version 用队列里拿到的 version_id，过期会返回 409 VERSION_CONFLICT。
 */
export function createReview(
  resourceId: number,
  payload: ReviewCreatePayload,
): Promise<ReviewResult> {
  return request<ReviewResult>(`/resources/${resourceId}/reviews`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** GET /resources/{id}/reviews —— 资源本人、课程负责人或管理员查看审核历史。 */
export function listResourceReviews(
  resourceId: number,
  params: { page?: number; page_size?: number } = {},
): Promise<Page<Review>> {
  const query = new URLSearchParams()
  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.page_size !== undefined) query.set('page_size', String(params.page_size))
  const suffix = query.toString()
  return request<Page<Review>>(
    `/resources/${resourceId}/reviews${suffix ? `?${suffix}` : ''}`,
  )
}
