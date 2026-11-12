import type { UserRole } from '../types/user'

/**
 * 各角色登录后的落地页。
 */
export function homeForRole(role: UserRole): string {
  if (role === 'admin') return '/admin'
  if (role === 'teacher') return '/teacher'
  return '/'
}
