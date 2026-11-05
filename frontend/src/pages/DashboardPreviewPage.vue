<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '../components/common/BaseCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import StatCard from '../components/common/StatCard.vue'
import TeacherLayout from '../layouts/TeacherLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'

const props = defineProps<{ role: 'teacher' | 'admin' }>()
const isTeacher = computed(() => props.role === 'teacher')
const layout = computed(() => isTeacher.value ? TeacherLayout : AdminLayout)
const stats = computed(() => isTeacher.value
  ? ['资源总数', '待审核', '已发布', '被驳回']
  : ['资源总数', '待审核', '用户总数', '总访问量'])
</script>

<template>
  <component :is="layout">
    <div class="page-heading">
      <div>
        <p>Learn-Hub · {{ isTeacher ? 'Teacher' : 'Admin' }}</p>
        <h1>{{ isTeacher ? '教师工作台' : '首页概览' }}</h1>
        <span>布局与卡片模板预览；业务接口接入后显示真实数据。</span>
      </div>
      <RouterLink to="/" class="back-link">返回学生首页</RouterLink>
    </div>

    <div class="stats-grid">
      <StatCard v-for="label in stats" :key="label" :label="label" state="unavailable" />
    </div>

    <div class="content-grid" :class="{ 'content-grid--admin': !isTeacher }">
      <BaseCard>
        <template #title>
          <h2>{{ isTeacher ? '最近共享的资源' : '访问趋势' }}</h2>
        </template>
        <EmptyState :title="isTeacher ? '还没有资源数据' : '统计数据暂未接入'"
          :description="isTeacher ? '接入本人资源接口后显示最近记录。' : '等统计口径和接口确定后再呈现趋势。'" />
      </BaseCard>
      <BaseCard>
        <template #title>
          <h2>{{ isTeacher ? '最近的审核结果' : '资源类型分布' }}</h2>
        </template>
        <EmptyState :title="isTeacher ? '还没有审核反馈' : '统计数据暂未接入'"
          :description="isTeacher ? '审核通知接入后显示最近反馈。' : '类型分布将按文档、视频、链接统计。'" />
      </BaseCard>
    </div>

    <BaseCard class="wide-card">
      <template #title>
        <h2>{{ isTeacher ? '资源访问趋势' : '待审核资源' }}</h2>
      </template>
      <EmptyState :title="isTeacher ? '统计数据暂未接入' : '审核队列尚未接入'"
        :description="isTeacher ? '后端提供统计接口后显示趋势。' : '接入审核接口后显示授权范围内的待审资源。'" />
    </BaseCard>
  </component>
</template>

<style scoped>
.page-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.page-heading p {
  margin: 0 0 6px;
  color: var(--lh-primary);
  font-size: 12px;
  font-weight: 700;
}

.page-heading h1 {
  margin: 0 0 8px;
  font-size: 30px;
  line-height: 40px;
}

.page-heading span {
  color: var(--lh-text-secondary);
  font-size: 14px;
}

.back-link {
  flex: none;
  padding: 10px 14px;
  border: 1px solid var(--lh-primary-border);
  border-radius: 8px;
  color: var(--lh-primary);
  font-size: 13px;
  text-decoration: none;
}

.back-link:hover {
  background: var(--lh-primary-soft);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 16px;
  margin-top: 16px;
}

.content-grid--admin {
  grid-template-columns: 7fr 5fr;
}

.wide-card {
  margin-top: 16px;
}

@media (max-width: 1023px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .page-heading {
    align-items: start;
    flex-direction: column;
  }

  .page-heading h1 {
    font-size: 24px;
    line-height: 34px;
  }
}
</style>
