<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { clearSession, useSession } from '../../api/session'

/*
 * 右上角账号入口：头像 + 显示名，点开是账号卡片 + 操作。
 * 头像用品牌蓝实心圆 + 名字首字（中文一个字、英文大写首字母），不依赖头像图片。
 * 令牌只存在内存里，退出即清空并回登录页。
 */
const router = useRouter()
const { currentUser } = useSession()
/** 菜单里点「我的收藏」跳转后要收起浮层，否则新页面上还挂着一张卡片 */
const menuOpen = ref(false)

const initial = computed(() => {
  const name = currentUser.value?.display_name?.trim() ?? ''
  const first = Array.from(name)[0] ?? ''
  return first ? first.toUpperCase() : '?'
})

const role = computed(() => currentUser.value?.role ?? 'student')

const roleLabel = computed(() => {
  if (role.value === 'admin') return '管理员'
  if (role.value === 'teacher') return '教师'
  return '学生'
})

const roleColor = computed(() => {
  if (role.value === 'admin') return 'primary' as const
  if (role.value === 'teacher') return 'info' as const
  return 'neutral' as const
})

async function logout(): Promise<void> {
  clearSession()
  await router.push({ name: 'login' })
}
</script>

<template>
  <UPopover v-model:open="menuOpen" :content="{ align: 'end', sideOffset: 8 }" :ui="{ content: 'w-[272px] p-0' }">
    <UButton
      color="neutral"
      variant="ghost"
      size="md"
      class="user-menu"
      :aria-label="`账号菜单：${currentUser?.display_name ?? ''}`"
    >
      <UAvatar
        :text="initial"
        size="md"
        :ui="{ root: 'bg-primary', fallback: 'text-white font-semibold' }"
      />
      <span class="user-menu__name">{{ currentUser?.display_name }}</span>
      <UIcon name="i-lucide-chevron-down" class="user-menu__chevron" aria-hidden="true" />
    </UButton>

    <template #content>
      <div class="user-card">
        <UAvatar
          :text="initial"
          size="xl"
          :ui="{ root: 'bg-primary', fallback: 'text-white font-semibold' }"
        />
        <div class="user-card__text">
          <div class="user-card__line">
            <p class="user-card__name">{{ currentUser?.display_name }}</p>
            <UBadge :color="roleColor" variant="soft" size="sm" class="user-card__role">
              {{ roleLabel }}
            </UBadge>
          </div>
        </div>
      </div>

      <USeparator />

      <div class="user-actions">
        <UButton v-if="role === 'student'" to="/my-submissions" color="neutral" variant="ghost" icon="i-lucide-file-up" block class="user-actions__item" @click="menuOpen = false">我的投稿</UButton>
        <UButton to="/favorites" color="neutral" variant="ghost" icon="i-lucide-bookmark" block class="user-actions__item" @click="menuOpen = false">我的收藏</UButton>
        <UButton v-if="role !== 'admin'" to="/learning" color="neutral" variant="ghost" icon="i-lucide-book-open-check" block class="user-actions__item" @click="menuOpen = false">学习进度</UButton>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-log-out"
          block
          class="user-actions__item"
          @click="logout"
        >
          退出登录
        </UButton>
      </div>
    </template>
  </UPopover>
</template>

<style scoped>
.user-menu {
  gap: 8px;
  height: 40px;
  padding: 0 10px 0 4px;
  border-radius: 999px;
  font-weight: 400;
}

.user-menu__name {
  max-width: 160px;
  overflow: hidden;
  color: var(--lh-text);
  font-size: 14px;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.user-menu__chevron {
  width: 14px;
  height: 14px;
  color: var(--lh-text-secondary);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.user-card__text {
  min-width: 0;
}

.user-card__line {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.user-card__name {
  margin: 0;
  overflow: hidden;
  color: var(--lh-text);
  font-size: 15px;
  font-weight: 600;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.user-card__role {
  flex: none;
}

.user-actions {
  padding: 8px;
}

.user-actions__item {
  justify-content: flex-start;
}

@media (max-width: 767px) {
  .user-menu {
    padding: 0 4px;
  }

  .user-menu__name,
  .user-menu__chevron {
    display: none;
  }
}
</style>
