/**
 * 学习进度相关的类型。
 * 字段与后端 app/schemas/learning.py 一一对应；后端改字段时这里要同步改。
 */

import type { ResourceStatus, ResourceType } from './resource'

/** 对应 LearningRecordPublic。 */
export interface LearningRecord {
  id: number
  resource_id: number
  /** 0–100 的整数，最后一次成功写入的值 */
  progress: number
  /** ISO 8601 UTC 字符串 */
  last_accessed_at: string
  created_at: string
  updated_at: string
}

/**
 * 学习记录里的资源引用（对应 LearningRecordResource）。
 *
 * 和 Resource 的区别：资源下架后这里**仍然有**标题、课程、分类，
 * 只是 is_available 为 false 且 url 为 null —— 用来"认出学过哪一份"，
 * 而不是继续提供内容入口。
 */
export interface LearningRecordResource {
  id: number
  title: string
  resource_type: ResourceType
  course_id: number
  course_title: string
  category_id: number
  category_name: string
  status: ResourceStatus
  is_available: boolean
  /** 资源不可公开访问时为 null */
  url: string | null
}

export interface LearningRecordItem extends LearningRecord {
  resource: LearningRecordResource
}

export interface LearningRecordPage {
  items: LearningRecordItem[]
  total: number
  page: number
  page_size: number
}
