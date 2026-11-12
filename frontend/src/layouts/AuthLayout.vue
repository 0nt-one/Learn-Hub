<script setup lang="ts">
/*
 * 认证页外壳（登录 / 注册共用）：品牌 + 插画 + 右侧卡片。
 * 页面只往默认插槽里放标题和表单，布局与背景集中在这里。
 */
import AppBrand from '../components/common/AppBrand.vue'
import AuthIllustration from '../components/illustrations/AuthIllustration.vue'

withDefaults(defineProps<{ labelledBy?: string }>(), { labelledBy: undefined })
</script>

<template>
  <main class="auth-page">
    <header class="auth-header">
      <AppBrand />
    </header>

    <div class="auth-content">
      <section class="auth-visual" aria-hidden="true">
        <AuthIllustration class="auth-visual__art" />
      </section>

      <section class="auth-panel" :aria-labelledby="labelledBy">
        <slot />
      </section>
    </div>
  </main>
</template>

<style scoped>
.auth-page {
  position: relative;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  min-height: 100svh;
  overflow: clip;
  background:
    radial-gradient(ellipse at 0% 52%, rgb(221 239 255 / 70%) 0%, transparent 48%),
    radial-gradient(ellipse at 22% 94%, rgb(219 237 255 / 55%) 0%, transparent 46%),
    #fff;
}

.auth-header {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px clamp(24px, 4vw, 56px) 0;
}

.auth-header :deep(.brand) {
  font-size: 24px;
  gap: 12px;
}

.auth-header :deep(.brand__mark) {
  transform: scale(1.05);
}

.auth-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: center;
  gap: clamp(16px, 1.5vw, 24px);
  flex: 1;
  min-height: 0;
  width: min(100%, 1440px);
  margin: 0 auto;
  padding: 20px clamp(24px, 4vw, 56px) 32px 24px;
}

.auth-visual {
  min-width: 0;
  align-self: stretch;
  display: flex;
  align-items: center;
}

.auth-visual__art {
  width: calc(100% + 32px);
  max-width: none;
  max-height: calc(100svh - 120px);
  margin-left: -16px;
  flex-shrink: 0;
}

.auth-panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 560px;
  justify-self: center;
  padding: clamp(28px, 3vw, 40px);
  border: 1px solid var(--lh-border);
  border-radius: 24px;
  background: rgb(255 255 255 / 96%);
  box-shadow: 0 24px 64px rgb(26 67 122 / 8%), 0 3px 10px rgb(26 67 122 / 4%);
}

@media (max-width: 959px) {
  .auth-header {
    padding: 28px 24px 0;
  }

  .auth-content {
    grid-template-columns: minmax(0, 1fr);
    padding: 36px 24px 48px;
  }

  .auth-visual {
    display: none;
  }

  .auth-panel {
    max-width: 520px;
    padding: 36px;
    margin-bottom: 0;
  }
}

@media (max-width: 479px) {
  .auth-header {
    padding: 24px 20px 0;
  }

  .auth-header :deep(.brand) {
    font-size: 23px;
  }

  .auth-content {
    padding: 32px 16px;
    align-items: start;
  }

  .auth-panel {
    padding: 28px 22px;
    border-radius: 20px;
  }
}
</style>

<!--
  卡片内部的排版由所有认证页共用：类名统一带 auth- 前缀，
  所以这里用非 scoped 样式，避免每个页面各抄一份。
-->
<style>
.auth-panel__title {
  margin: 0;
  color: var(--lh-text);
  font-size: clamp(32px, 2.7vw, 40px);
  font-weight: 750;
  line-height: 1.2;
  letter-spacing: -0.035em;
}

.auth-panel__brand {
  color: var(--lh-primary);
  font-size: 1.05em;
  letter-spacing: -0.045em;
}

.auth-panel__subtitle {
  margin: 12px 0 28px;
  color: var(--lh-text-secondary);
  font-size: 16px;
  line-height: 25px;
}

.auth-form {
  display: grid;
  gap: 16px;
}

.auth-submit,
.auth-switch {
  min-height: 48px;
  justify-content: center;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
}

.auth-submit {
  margin-top: 8px;
}

.auth-error {
  margin: 0;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--lh-danger-soft);
  color: var(--lh-danger);
  font-size: 13px;
  line-height: 20px;
}

.auth-panel__footer {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  color: var(--lh-text-dimmed);
  font-size: 12px;
  text-align: center;
  line-height: 20px;
}

.auth-panel__footer span {
  height: 1px;
  flex: 1;
  background: var(--lh-border);
}

@media (max-width: 479px) {
  .auth-panel__title {
    font-size: 30px;
  }

  .auth-panel__subtitle {
    font-size: 14px;
    margin-bottom: 28px;
  }
}
</style>
