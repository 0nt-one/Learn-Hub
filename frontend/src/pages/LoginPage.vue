<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/auth'
import { ApiError } from '../api/client'
import { setSession } from '../api/session'
import { homeForRole } from '../router/home'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const route = useRoute()

const state = reactive({ username: '', password: '' })
const serverError = ref('')
const showPassword = ref(false)

/** 规则与后端一致：用户名 3–32 位字母/数字/下划线，密码 12–128 位 */
function validate(values: { username: string; password: string }): { name: string; message: string }[] {
    const errors: { name: string; message: string }[] = []
    const username = values.username.trim()

    if (username.length < 3) {
        errors.push({ name: 'username', message: '用户名至少 3 个字符' })
    } else if (!/^[A-Za-z0-9_]+$/.test(username)) {
        errors.push({ name: 'username', message: '只能包含字母、数字和下划线' })
    }

    if (values.password.length < 12) {
        errors.push({ name: 'password', message: '密码至少 12 位' })
    }

    return errors
}

/**
 * 站内相对路径判定，用于登录后的返回地址，防止开放重定向。
 * 拒绝 "https://evil.com"、"//evil.com"（协议相对 URL）和含反斜杠的写法
 * （部分浏览器把 \ 当作 /，"/\evil.com" 会跳到外站）。
 */
function isSafeInternalPath(value: unknown): value is string {
    return typeof value === 'string'
        && value.startsWith('/')
        && !value.startsWith('//')
        && !value.includes('\\')
}

async function onSubmit(): Promise<void> {
    serverError.value = ''

    try {
        const token = await login({
            username: state.username.trim().toLowerCase(),
            password: state.password,
        })
        setSession(token)
        // 只接受站内相对路径，登录后回到原来的页面（含各角色工作台）。
        const redirect = route.query.redirect
        await router.push(isSafeInternalPath(redirect) ? redirect : homeForRole(token.user.role))
    } catch (e) {
        serverError.value = e instanceof ApiError ? e.message : '登录失败，请稍后重试。'
    }
}
</script>

<template>
    <AuthLayout labelled-by="login-title">
        <h1 id="login-title" class="auth-panel__title">
            Welcome to <span class="auth-panel__brand">Learn-Hub</span>
        </h1>
        <p class="auth-panel__subtitle">欢迎登录，继续你的学习之旅。</p>

        <UForm class="auth-form" :state="state" :validate="validate" @submit="onSubmit">
            <UFormField name="username" required>
                <UInput v-model="state.username" class="w-full"
                    :ui="{ base: 'h-12 rounded-lg text-[15px]', leadingIcon: 'text-primary size-5' }"
                    icon="i-lucide-user-round" size="xl" name="username" autocomplete="username" :maxlength="32"
                    placeholder="用户名" />
            </UFormField>

            <UFormField name="password" required>
                <UInput v-model="state.password" class="w-full"
                    :ui="{ base: 'h-12 rounded-lg text-[15px]', leadingIcon: 'text-primary size-5' }"
                    :type="showPassword ? 'text' : 'password'" icon="i-lucide-lock-keyhole" size="xl"
                    name="password" autocomplete="current-password" :maxlength="128" placeholder="密码">
                    <template #trailing>
                        <UButton type="button" color="neutral" variant="ghost" class="size-10 justify-center"
                            :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                            :aria-label="showPassword ? '隐藏密码' : '显示密码'" :aria-pressed="showPassword"
                            @click="showPassword = !showPassword" />
                    </template>
                </UInput>
            </UFormField>

            <p v-if="serverError" class="auth-error" role="alert">{{ serverError }}</p>

            <UButton type="submit" color="primary" size="xl" class="auth-submit" block>登录</UButton>
            <UButton to="/register" color="primary" variant="outline" size="xl" class="auth-switch" block>
                创建账号
            </UButton>
        </UForm>

        <div class="auth-panel__footer"><span></span> 知汇 —— 让智慧发生，让知识汇聚 <span></span></div>
    </AuthLayout>
</template>
