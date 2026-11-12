import { request } from './client'
import type { LoginPayload, RegisterPayload, Token, User } from '../types/user'

export function login(payload: LoginPayload): Promise<Token> {
  return request<Token>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * 注册只返回用户，**不返回令牌**（后端 201 UserEnvelope）。
 * 想让用户注册完直接进入系统，需要在调用方紧接着再调一次 login。
 */
export function register(payload: RegisterPayload): Promise<User> {
  return request<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
