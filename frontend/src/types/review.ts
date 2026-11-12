/**
 * 审核相关类型，对应后端 app/schemas/review.py。
 * 审核记录是不可变的：一次决定对应一条记录，绑定当时的资源版本。
 */
import type { Resource } from './resource'

export type ReviewDecision = 'approved' | 'rejected'

/** 对应 ReviewPublic。 */
export interface Review {
  id: number
  resource_id: number
  reviewer_id: number
  /** 审核时的资源版本，用来对账"审的是哪一版" */
  resource_version: number
  decision: ReviewDecision
  comment: string
  created_at: string
}

/** 对应 ReviewResult：审核记录 + 审核后的资源快照。 */
export interface ReviewResult {
  review: Review
  resource: Resource
}

/**
 * 对应 ReviewCreateRequest。
 * 驳回时 comment 必填（后端会拒绝空意见），通过时可留空。
 */
export interface ReviewCreatePayload {
  expected_version: number
  decision: ReviewDecision
  comment?: string
}
