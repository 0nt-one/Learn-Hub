/**
 * 资源相关的前端枚举，与 docs/api-contract.md 的 Resource DTO 保持一致。
 * 这里只放展示与状态判断需要的字段；完整 DTO 等接入接口时再补。
 */
export type ResourceStatus = 'draft' | 'pending' | 'approved' | 'rejected' | 'archived'

export type ResourceType = 'document' | 'video' | 'link'

/** 列表与卡片需要的展示字段。课程/分类名称由授权字典解析，拿不到时为 null，不虚构。 */
export interface ResourceSummary {
  isFavorited?: boolean
  id: number
  title: string
  description: string | null
  resourceType: ResourceType
  courseName: string | null
  categoryName: string | null
  /** UTC ISO 8601 字符串；页面按本地时区显示 */
  updatedAt: string | null
}

/** 资源中心首版只支持“最新 / 标题”两种排序（契约 sort 参数）。 */
export type ResourceSort = 'newest' | 'title'

/** 首版每维单选；null 表示“全部”，不传该维参数。 */
export interface ResourceFilters {
  courseId: number | null
  categoryId: number | null
  type: ResourceType | null
}

/**
 * 对应后端 ResourcePublic。
 * 后端返回已授权资源的课程和分类名称。
 */
export interface Resource {
  id: number
  title: string
  description: string
  resource_type: ResourceType
  url: string
  duration_seconds: number | null
  page_count: number | null
  course_id: number
  course_title: string
  course_teacher_id: number
  course_teacher_display_name: string
  category_id: number
  category_name: string
  owner_id: number
  owner_display_name: string
  /** 当前登录用户是否已收藏；不表示资源当前仍可新增收藏。 */
  is_favorited: boolean
  status: ResourceStatus
  /** 乐观锁版本号，提交审核时需要回传 */
  version_id: number
  created_at: string
  updated_at: string
}

/**
 * 对应 ResourceCreateRequest。
 * 元数据规则由后端按类型校验（resource_validation.py）：
 * - video：duration_seconds 必填且 > 0，page_count 必须为空
 * - document：duration_seconds 必须为空，page_count 可选且 > 0
 * - link：两者都必须为空
 */
export interface ResourceCreatePayload {
  title: string
  description?: string
  resource_type: ResourceType
  url: string
  duration_seconds?: number | null
  page_count?: number | null
  course_id: number
  category_id: number
}

/**
 * 对应 ResourceUpdateRequest：字段全部可选，但必须带 expected_version（乐观锁）。
 * 后端只允许资源本人在 draft / rejected 状态下修改。
 */
export interface ResourceUpdatePayload {
  expected_version: number
  title?: string
  description?: string
  resource_type?: ResourceType
  url?: string
  duration_seconds?: number | null
  page_count?: number | null
  course_id?: number
  category_id?: number
}
