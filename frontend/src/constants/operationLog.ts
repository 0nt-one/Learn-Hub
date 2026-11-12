/**
 * 操作日志的动作代码与对象类型映射。
 *
 * 后端写入的是稳定的英文代码（见 app/services 里的 action=...），
 * 展示层翻译成中文；未收录的新动作回落显示原始代码，
 * 所以后端新增日志动作不需要同步改前端。
 */

export type LogBadgeColor = 'success' | 'neutral' | 'info' | 'primary' | 'warning'

export const ACTION_LABELS: Record<string, string> = {
  'user.update': '修改用户',
  'category.create': '创建分类',
  'category.update': '修改分类',
  'course.create': '创建课程',
  'course.update': '修改课程',
  'resource.create': '创建资源',
  'resource.update': '修改资源',
  'resource.submit': '提交审核',
  'resource.withdraw': '撤回资源',
  'resource.archive': '归档资源',
  'resource.review': '审核资源',
}

/** 按动作语义着色，方便在长列表里快速扫读 */
export const ACTION_COLORS: Record<string, LogBadgeColor> = {
  'user.update': 'neutral',
  'category.create': 'success',
  'category.update': 'neutral',
  'course.create': 'success',
  'course.update': 'neutral',
  'resource.create': 'success',
  'resource.update': 'neutral',
  'resource.submit': 'info',
  'resource.withdraw': 'warning',
  'resource.archive': 'warning',
  'resource.review': 'primary',
}

export const TARGET_LABELS: Record<string, string> = {
  user: '用户',
  course: '课程',
  category: '分类',
  resource: '资源',
}

export function targetLabel(value: string): string {
  return TARGET_LABELS[value] ?? value
}
