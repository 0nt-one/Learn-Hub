<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '../api/auth'
import { ApiError } from '../api/client'
import { setSession } from '../api/session'
import { homeForRole } from '../router/home'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()

const state = reactive({
    username: '',
    displayName: '',
    password: '',
    confirm: '',
})
const serverError = ref('')
const showPassword = ref(false)

/** 规则与后端一致：用户名 3–32 位字母/数字/下划线，显示名 1–64，密码 12–128 位 */
function validate(values: typeof state): { name: string; message: string }[] {
    const errors: { name: string; message: string }[] = []
    const username = values.username.trim()

    if (username.length < 3) {
        errors.push({ name: 'username', message: '用户名至少 3 个字符' })
    } else if (!/^[A-Za-z0-9_]+$/.test(username)) {
        errors.push({ name: 'username', message: '只能包含字母、数字和下划线' })
    }

    if (values.displayName.trim().length < 1) {
        errors.push({ name: 'displayName', message: '请填写显示名' })
    } else if (values.displayName.trim().length > 64) {
        errors.push({ name: 'displayName', message: '显示名最多 64 个字符' })
    }

    if (values.password.length < 12) {
        errors.push({ name: 'password', message: '密码至少 12 位' })
    }

    if (values.confirm !== values.password) {
        errors.push({ name: 'confirm', message: '两次输入的密码不一致' })
    }

    return errors
}

async function onSubmit(): Promise<void> {
    serverError.value = ''

    const username = state.username.trim().toLowerCase()
    const password = state.password

    try {
        await register({
            username,
            password,
            display_name: state.displayName.trim(),
        })

        // 注册接口不发令牌，所以紧接着登录一次，用户不用手动再输一遍
        const token = await login({ username, password })
        setSession(token)
        await router.push(homeForRole(token.user.role))
    } catch (e) {
        serverError.value = e instanceof ApiError ? e.message : '注册失败，请稍后重试。'
    }
}
</script>

<template>
    <AuthLayout labelled-by="register-title">
        <h1 id="register-title" class="auth-panel__title">
            Join <span class="auth-panel__brand">Learn-Hub</span>
        </h1>
        <p class="auth-panel__subtitle">创建账号，开始整理你的学习资源。</p>

        <UForm class="auth-form" :state="state" :validate="validate" @submit="onSubmit">
            <UFormField name="username" required>
                <UInput v-model="state.username" class="w-full"
                    :ui="{ base: 'h-12 rounded-lg text-[15px]', leadingIcon: 'text-primary size-5' }"
                    icon="i-lucide-user-round" size="xl" name="username" autocomplete="username" :maxlength="32"
                    placeholder="用户名" />
            </UFormField>

            <UFormField name="displayName" required>
                <UInput v-model="state.displayName" class="w-full"
                    :ui="{ base: 'h-12 rounded-lg text-[15px]', leadingIcon: 'text-primary size-5' }"
                    icon="i-lucide-user" size="xl" name="displayName" autocomplete="nickname" :maxlength="64"
                    placeholder="显示名（别人看到的名字）" />
            </UFormField>

            <UFormField name="password" required>
                <UInput v-model="state.password" class="w-full"
                    :ui="{ base: 'h-12 rounded-lg text-[15px]', leadingIcon: 'text-primary size-5' }"
                    :type="showPassword ? 'text' : 'password'" icon="i-lucide-lock-keyhole" size="xl"
                    name="password" autocomplete="new-password" :maxlength="128" placeholder="密码（至少 12 位）">
                    <template #trailing>
                        <UButton type="button" color="neutral" variant="ghost" class="size-10 justify-center"
                            :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                            :aria-label="showPassword ? '隐藏密码' : '显示密码'" :aria-pressed="showPassword"
                            @click="showPassword = !showPassword" />
                    </template>
                </UInput>
            </UFormField>

            <UFormField name="confirm" required>
                <UInput v-model="state.confirm" class="w-full"
                    :ui="{ base: 'h-12 rounded-lg text-[15px]', leadingIcon: 'text-primary size-5' }"
                    :type="showPassword ? 'text' : 'password'" icon="i-lucide-lock" size="xl" name="confirm"
                    autocomplete="new-password" :maxlength="128" placeholder="再输一次密码" />
            </UFormField>

            <p v-if="serverError" class="auth-error" role="alert">{{ serverError }}</p>

            <UButton type="submit" color="primary" size="xl" class="auth-submit" block>创建账号</UButton>
            <UButton to="/login" color="primary" variant="outline" size="xl" class="auth-switch" block>
                已有账号，去登录
            </UButton>
        </UForm>

        <div class="auth-panel__footer"><span></span> 知汇 —— 让智慧发生，让知识汇聚 <span></span></div>
    </AuthLayout>
</template>
