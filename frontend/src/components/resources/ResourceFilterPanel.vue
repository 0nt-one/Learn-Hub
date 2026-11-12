<script setup lang="ts">
import { computed, useId } from 'vue'
import type { ResourceFilters, ResourceType } from '../../types/resource'

const props = defineProps<{
  modelValue: ResourceFilters
  courses: { id: number; title: string }[]
  categories: { id: number; name: string }[]
  coursesMore: boolean
  categoriesMore: boolean
  coursesLoading: boolean
  categoriesLoading: boolean
  coursesError: string
  categoriesError: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: ResourceFilters]
  reset: []
  loadCourses: []
  loadCategories: []
}>()
const id = useId()
const courses = computed(() => [
  { label: '全部课程', value: 0 },
  ...props.courses.map(c => ({ label: c.title, value: c.id })),
  ...(props.modelValue.courseId && !props.courses.some(c => c.id === props.modelValue.courseId)
    ? [{ label: `课程 #${props.modelValue.courseId}`, value: props.modelValue.courseId }] : []),
])
const categories = computed(() => [
  { label: '全部分类', value: 0 },
  ...props.categories.map(c => ({ label: c.name, value: c.id })),
  ...(props.modelValue.categoryId && !props.categories.some(c => c.id === props.modelValue.categoryId)
    ? [{ label: `分类 #${props.modelValue.categoryId}`, value: props.modelValue.categoryId }] : []),
])
const types: { value: ResourceType | null; label: string }[] = [
  { value: null, label: '全部类型' }, { value: 'document', label: '文档' },
  { value: 'video', label: '视频' }, { value: 'link', label: '链接' },
]
</script>

<template>
  <section class="filters" :aria-labelledby="`${id}-title`">
    <header><h2 :id="`${id}-title`">筛选资源</h2><UButton variant="ghost" color="neutral" size="sm" @click="emit('reset')">重置</UButton></header>
    <div class="group">
      <label :for="`${id}-course`">课程</label>
      <USelectMenu :id="`${id}-course`" :model-value="modelValue.courseId ?? 0" :items="courses" value-key="value"
        :loading="coursesLoading" class="w-full"
        :search-input="{ placeholder: '搜索已加载课程', variant: 'outline', icon: 'i-lucide-search' }"
        :ui="{ input: 'm-2 border-0' }"
        @update:model-value="emit('update:modelValue', { ...modelValue, courseId: $event || null })" />
      <p v-if="coursesError" role="alert">{{ coursesError }}</p>
      <UButton v-if="coursesMore || coursesError" variant="link" :loading="coursesLoading" @click="emit('loadCourses')">{{ coursesError ? '重试加载课程' : '加载更多课程' }}</UButton>
    </div>
    <fieldset class="group">
      <legend>资源类型</legend>
      <button v-for="option in types" :key="option.label" class="type-option" type="button"
        :aria-pressed="modelValue.type === option.value"
        @click="emit('update:modelValue', { ...modelValue, type: option.value })">{{ option.label }}</button>
    </fieldset>
    <div class="group">
      <label :for="`${id}-category`">分类</label>
      <USelectMenu :id="`${id}-category`" :model-value="modelValue.categoryId ?? 0" :items="categories" value-key="value"
        :loading="categoriesLoading" class="w-full"
        :search-input="{ placeholder: '搜索已加载分类', variant: 'outline', icon: 'i-lucide-search' }"
        :ui="{ input: 'm-2 border-0' }"
        @update:model-value="emit('update:modelValue', { ...modelValue, categoryId: $event || null })" />
      <p v-if="categoriesError" role="alert">{{ categoriesError }}</p>
      <UButton v-if="categoriesMore || categoriesError" variant="link" :loading="categoriesLoading" @click="emit('loadCategories')">{{ categoriesError ? '重试加载分类' : '加载更多分类' }}</UButton>
    </div>
  </section>
</template>

<style scoped>
.filters { display: grid; gap: 24px; padding: 20px; border: 1px solid var(--lh-border); border-radius: 12px; background: var(--lh-surface); }
header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
h2 { margin: 0; font-size: 16px; font-weight: 600; }
.group { display: grid; gap: 10px; min-width: 0; margin: 0; padding: 0; border: 0; }
label, legend { font-size: 13px; font-weight: 600; }
legend { margin-bottom: 10px; }
.group p { margin: 0; color: var(--lh-danger); font-size: 12px; }
.type-option { min-height: 40px; border-radius: 8px; padding: 8px 12px; text-align: left; color: var(--lh-text-secondary); font-size: 14px; }
.type-option:hover { background: var(--lh-surface-subtle); }
.type-option[aria-pressed="true"] { color: var(--lh-primary); background: var(--lh-primary-soft); font-weight: 600; }
</style>
