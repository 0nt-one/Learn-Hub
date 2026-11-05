<script setup lang="ts">
defineProps<{
  items: readonly { label: string; to?: string }[]
}>()
</script>

<template>
  <nav v-if="items.length > 1" class="breadcrumbs" aria-label="面包屑导航">
    <ol>
      <li v-for="(item, index) in items" :key="index">
        <RouterLink v-if="item.to && index < items.length - 1" :to="item.to">
          {{ item.label }}
        </RouterLink>
        <span v-else :aria-current="index === items.length - 1 ? 'page' : undefined">
          {{ item.label }}
        </span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.breadcrumbs {
  margin-bottom: 16px;
  color: var(--lh-text-secondary);
  font-size: 13px;
}

ol {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

li {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

li+li::before {
  content: '/';
  color: var(--lh-control-border);
}

a {
  border-radius: 3px;
  color: var(--lh-text-secondary);
  text-decoration: none;
}

a:hover {
  color: var(--lh-primary);
  text-decoration: underline;
}

[aria-current="page"] {
  color: var(--lh-text);
  font-weight: 600;
}
</style>
