import { request } from './client'
import type { Page } from '../types/api'
import type { Course, CourseCreatePayload, CourseUpdatePayload } from '../types/course'

export interface CourseListParams {
  page?: number
  page_size?: number
  /** 按课程标题搜索，1–100 字符 */
  q?: string
  /** null / undefined 表示不筛选；普通列表对非管理员的停用筛选返回 403 */
  is_active?: boolean | null
}

function courseListSuffix(params: CourseListParams): string {
  const query = new URLSearchParams()

  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.page_size !== undefined) query.set('page_size', String(params.page_size))
  if (params.q) query.set('q', params.q)
  if (params.is_active !== undefined && params.is_active !== null) {
    query.set('is_active', String(params.is_active))
  }

  const suffix = query.toString()
  return suffix ? `?${suffix}` : ''
}

/** GET /courses —— 分页查询。非管理员只能看到启用课程。 */
export function listCourses(params: CourseListParams = {}): Promise<Page<Course>> {
  const suffix = courseListSuffix(params)
  return request<Page<Course>>(`/courses${suffix}`)
}

/** GET /courses/mine —— 当前教师负责的课程，默认包含停用课程。 */
export function listMyCourses(params: CourseListParams = {}): Promise<Page<Course>> {
  const suffix = courseListSuffix(params)
  return request<Page<Course>>(`/courses/mine${suffix}`)
}

/** POST /courses —— 教师/管理员创建，代码重复返回 409 COURSE_CODE_EXISTS。 */
export function createCourse(payload: CourseCreatePayload): Promise<Course> {
  return request<Course>('/courses', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** PATCH /courses/{id} —— 负责人或管理员修改，至少提交一个字段。 */
export function updateCourse(id: number, payload: CourseUpdatePayload): Promise<Course> {
  return request<Course>(`/courses/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
