import { getAccessToken } from './session'

const BASE_URL = '/api/v1'
const TIMEOUT_MS = 8000

/**
 * 会话失效（带着令牌仍收到 401）的回调。
 * 由 main.ts 注入，避免 client → router → pages → client 的循环导入。
 */
let unauthorizedHandler: (() => void) | null = null

export function setUnauthorizedHandler(handler: () => void): void {
  unauthorizedHandler = handler
}

/**
 * 所有失败都归一到这个类型
 */
export class ApiError extends Error {
  /** HTTP 状态码；0 表示请求根本没到服务器（断网、超时） */
  readonly status: number
  /** 后端稳定错误码，例如 INVALID_CREDENTIALS */
  readonly code: string
  /** 用于对日志排查；网络错误时为空字符串 */
  readonly requestId: string
  
  constructor(status: number, code: string, message: string, requestId: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}
interface ErrorBody {
  error?: {
    message?: string
    code?: string
  }
  /** 后端字段是 snake_case */
  request_id?: string
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  // 统一在这里加令牌：需要鉴权的接口不用各自记得带
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers,
      signal: AbortSignal.timeout(TIMEOUT_MS),
    })
  } catch {
    // 断网、超时、被中断：没有 HTTP 状态，也没有 request_id
    throw new ApiError(0, 'NETWORK_ERROR', '网络连接失败，请检查网络后重试。', '')
  }
  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    // 带着令牌仍被拒（401）：令牌过期或已失效，上抛回调让上层清会话并引导登录。
    // 判断 token 是否存在很关键——登录接口密码错误也返回 401，
    // 不判断会把用户从登录页踢走，连错误提示都丢掉。
    // 403 不在此列：那是"没权限"，不是"没身份"，清会话会让用户莫名其妙被登出。
    if (response.status === 401 && token) {
      unauthorizedHandler?.()
    }

    const failure = body as ErrorBody | null
    throw new ApiError(
      response.status,
      failure?.error?.code ?? 'UNKNOWN',
      failure?.error?.message ?? `请求失败。(HTTP ${response.status})`,
      failure?.request_id ?? response.headers.get('X-Request-Id') ?? '',
    )
  }

  const data = (body as { data: T }).data
  if (data === undefined) {
      throw new ApiError(response.status, 'INVALID_RESPONSE', '服务返回了无法识别的数据。', '')
  }
  return data
}