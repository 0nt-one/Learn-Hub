/**
 * 与 docs/api-contract.md 第 1、2 节对齐的通用响应类型。
 * 后端所有成功响应都包在 data 里，失败响应的形状是 { error, request_id }。
 */

/** 成功响应信封：{ "data": {...}, "request_id": "uuid" } */
export interface ApiEnvelope<T> {
  data: T
  request_id: string
}

/** 失败响应信封：{ "error": { code, message }, "request_id": "uuid" } */
export interface ApiErrorBody {
  error: {
    /** 稳定错误码，例如 USERNAME_EXISTS、INVALID_CREDENTIALS */
    code: string
    /** 可直接展示给用户的中文说明 */
    message: string
  }
  request_id: string
}

/** 已在后端或契约里出现的错误码，按需补充；不要用它做分支判断的唯一依据。 */
export type ApiErrorCode =
  | 'USERNAME_EXISTS'
  | 'INVALID_CREDENTIALS'
  | 'VALIDATION_ERROR'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'VERSION_CONFLICT'
  | 'SERVICE_UNAVAILABLE'

/** 分页响应里 data 的形状。 */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
