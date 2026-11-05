<template>
  <section class="base-card">
    <header v-if="$slots.title || $slots.eyebrow || $slots.action" class="base-card__header">
      <div>
        <p v-if="$slots.eyebrow" class="base-card__eyebrow">
          <slot name="eyebrow" />
        </p>
        <div class="base-card__title">
          <slot name="title" />
        </div>
      </div>
      <slot name="action" />
    </header>
    <div class="base-card__body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="base-card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped>
.base-card {
  min-width: 0;
  padding: 24px;
  border: 1px solid var(--lh-border);
  border-radius: 20px;
  background: var(--lh-surface);
  box-shadow: 0 4px 20px rgb(15 42 95 / 4%);
}

.base-card__header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.base-card__eyebrow {
  margin: 0 0 4px;
  color: var(--lh-primary);
  font-size: 12px;
  font-weight: 700;
}

.base-card__title :deep(h2),
.base-card__title :deep(h3) {
  margin: 0;
  font-size: 20px;
  line-height: 28px;
}

.base-card__footer {
  margin-top: 16px;
}

@media (max-width: 767px) {
  .base-card {
    padding: 16px;
  }
}
</style>
