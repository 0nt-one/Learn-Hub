
import { computed, ref } from 'vue'
import type { Token, User } from '../types/user'


/**
 *  第一版会话：令牌与当前用户只存在内存里，刷新页面即退出登录。
 */
const accessToken = ref<string | null>(null)
const currentUser = ref<User | null>(null)

export function setSession(token: Token): void {
    accessToken.value = token.access_token
    currentUser.value = token.user
}
export function clearSession(): void {
    accessToken.value = null
    currentUser.value = null
}

/**
 * 供 HTTP 客户端拼 Authorization 头使用。
 * 组件里不要直接调它，读状态请用 useSession()。
 */
export function getAccessToken(): string | null {
    return accessToken.value
}

export function useSession() {
    return {
        accessToken,
        currentUser,
        isLoggedIn: computed(() => accessToken.value !== null),
    }
}