/**
 * 分类相关类型，对应后端 app/schemas/category.py。
 * 分类是单层结构，名称唯一；资源必须归属一个课程和一个分类。
 */

/** 对应 CategoryPublic。 */
export interface Category {
  id: number
  name: string
  description: string
  is_active: boolean
  /** ISO 8601 UTC 字符串 */
  created_at: string
  updated_at: string
}

/** 对应 CategoryCreateRequest：名称 1–64，描述最多 1000。 */
export interface CategoryCreatePayload {
  name: string
  description?: string
}

/** 对应 CategoryUpdateRequest：至少一个字段，且不接受 null。 */
export interface CategoryUpdatePayload {
  name?: string
  description?: string
  is_active?: boolean
}
