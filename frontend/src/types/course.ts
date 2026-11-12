/**
 * 课程相关类型，对应后端 app/schemas/course.py。
 * 课程代码只有 ASCII 大写字母、数字和短横线，提交前会被 trim + 转大写。
 */

/** 对应 CoursePublic。 */
export interface Course {
  id: number
  code: string
  title: string
  description: string
  teacher_id: number
  teacher_display_name: string
  is_active: boolean
  /** ISO 8601 UTC 字符串 */
  created_at: string
  updated_at: string
}

/** 对应 CourseCreateRequest：教师创建时不传 teacher_id（后端固定本人），管理员必填。 */
export interface CourseCreatePayload {
  code: string
  title: string
  description?: string
  teacher_id?: number
}

/** 对应 CourseUpdateRequest：至少一个字段，且不接受 null。 */
export interface CourseUpdatePayload {
  code?: string
  title?: string
  description?: string
  is_active?: boolean
  teacher_id?: number
}
