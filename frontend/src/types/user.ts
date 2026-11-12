/**
 * 用户与认证相关的类型。
 * 字段与后端 app/schemas/user.py、app/schemas/auth.py 一一对应；
 * 后端改字段时，这个文件必须同步改（没有自动生成，别只改一边）。
 */

/** 对应后端 models/user.py 的 CHECK 约束。 */
export type UserRole = 'student' | 'teacher' | 'admin'

/** 对应 UserPublic。注意：不包含 password_hash，后端也不会返回。 */
export interface User {
  id: number
  username: string
  display_name: string
  role: UserRole
  is_active: boolean
  /** ISO 8601 UTC 字符串，例如 2026-11-06T02:04:35Z */
  created_at: string
  /** 同上 */
  updated_at: string
}

/** 对应 TokenPublic。 */
export interface Token {
  access_token: string
  token_type: 'bearer'
  /** 有效期（秒），后端当前为 30 分钟 */
  expires_in: number
  user: User
}

/** 对应 RegisterRequest；注册永远只能创建学生，不接受 role/display_name 之外的身份字段。 */
export interface RegisterPayload {
  username: string
  password: string
  display_name: string
}

/** 对应 LoginRequest。 */
export interface LoginPayload {
  username: string
  password: string
}

/**
 * 对应 UserUpdateRequest：至少提交一个字段，且不接受 null。
 * 管理员不能改自己的角色或停用自己（后端返回 409）。
 */
export interface UserUpdatePayload {
  role?: UserRole
  is_active?: boolean
}
