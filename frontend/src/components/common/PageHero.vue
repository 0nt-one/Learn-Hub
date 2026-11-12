<script setup lang="ts">
/*
 * 学生基础功能页的紧凑页头（收藏、学习进度）；资源中心保留独立展示横幅。
 * 只负责视觉，不产生语义；标题仍由内部的 PageHeader 输出的唯一 H1 承担。
 * 用法：把 PageHeader（以及需要贴着标题的说明行）放进默认插槽。
 */
</script>

<template>
  <section class="page-hero">
    <div class="page-hero__content">
      <slot />
    </div>
    <div class="page-hero__glow" aria-hidden="true">
      <span class="page-hero__bubble page-hero__bubble--primary" />
      <span class="page-hero__bubble page-hero__bubble--secondary" />
    </div>
  </section>
</template>

<style scoped>
.page-hero {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 124px;
  margin: 0 0 16px;
  padding: 12px 24% 12px 0;
  overflow: hidden;
  background: transparent;
}

.page-hero__content {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.page-hero :deep(.page-header) {
  margin: 0;
  padding: 0;
}
.page-hero :deep(.page-header__title) { font-size: 28px; line-height: 36px; }
.page-hero :deep(.page-header__eyebrow) { margin-bottom: 6px; font-size: 11px; line-height: 16px; }
.page-hero :deep(.page-header__description) { margin-top: 6px; }

.page-hero__glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.page-hero__bubble {
  position: absolute;
  border-radius: 50%;
}

.page-hero__bubble--primary {
  top: -70px;
  right: -28px;
  width: 220px;
  height: 220px;
  background: color-mix(in srgb, var(--lh-primary) 5%, transparent);
}

.page-hero__bubble--secondary {
  top: -105px;
  right: -4px;
  width: 160px;
  height: 160px;
  border: 1px solid color-mix(in srgb, var(--lh-primary) 6%, transparent);
  background: color-mix(in srgb, var(--lh-primary) 3%, transparent);
}

@media (max-width: 1023px) {
  .page-hero {
    min-height: 124px;
    padding: 12px 24% 12px 0;
  }

  .page-hero__bubble--primary {
    width: 200px;
    height: 200px;
    top: -70px;
  }

}

@media (max-width: 767px) {
  .page-hero {
    min-height: 0;
    margin-inline: 0;
    padding: 8px 0;
  }
  .page-hero :deep(.page-header__title) { font-size: 24px; line-height: 32px; }

  .page-hero__bubble--primary {
    top: -80px;
    right: -80px;
    width: 200px;
    height: 200px;
  }

  .page-hero__glow {
    display: none;
  }
}
</style>
