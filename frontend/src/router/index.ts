import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
    },
    {
      path: '/teacher',
      name: 'teacher-preview',
      component: () => import('../pages/DashboardPreviewPage.vue'),
      props: { role: 'teacher' },
    },
    {
      path: '/admin',
      name: 'admin-preview',
      component: () => import('../pages/DashboardPreviewPage.vue'),
      props: { role: 'admin' },
    },
  ],
})
