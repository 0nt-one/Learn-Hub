<script setup lang="ts">
import AppBrand from '../components/common/AppBrand.vue'
</script>

<template>
  <div class="student-layout">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <header class="student-header">
      <div class="student-header__inner">
        <AppBrand />
        <nav aria-label="学生导航">
          <RouterLink to="/" aria-current="page">发现</RouterLink>
        </nav>
        <span class="student-header__note">页面模板预览</span>
      </div>
    </header>
    <main id="main-content" class="student-main">
      <slot name="breadcrumb" />
      <slot />
    </main>
    <footer class="student-footer">Learn-Hub · 学习资源共享平台</footer>
  </div>
</template>

<style scoped>
.student-header {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 64px;
  border-bottom: 1px solid var(--lh-border);
  background: rgb(255 255 255 / 96%);
}

.student-header__inner {
  display: flex;
  align-items: center;
  gap: 56px;
  width: min(100%, 1440px);
  height: 100%;
  margin: auto;
  padding: 0 32px;
}

nav a {
  display: inline-block;
  padding: 9px 20px;
  border-radius: 999px;
  background: var(--lh-primary-soft);
  color: var(--lh-primary);
  font-weight: 600;
  text-decoration: none;
}

.student-header__note {
  margin-left: auto;
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--lh-surface-subtle);
  color: var(--lh-text-secondary);
  font-size: 12px;
}

.student-main {
  width: min(100%, 1440px);
  margin: auto;
  padding: 24px 32px 64px;
}

.student-footer {
  padding: 0 24px 28px;
  color: var(--lh-text-secondary);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 767px) {
  .student-header {
    height: 56px;
  }

  .student-header__inner {
    gap: 20px;
    padding: 0 16px;
  }

  .student-header__note {
    display: none;
  }

  nav a {
    padding: 7px 14px;
  }

  .student-main {
    padding: 16px 16px 40px;
  }
}
</style>
