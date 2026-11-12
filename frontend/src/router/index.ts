import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import { useSession } from '../api/session'
import type { UserRole } from '../types/user'
import { homeForRole } from './home'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    /** 需要登录才能进入；公开页面（首页、登录、注册）不写 */
    requiresAuth?: boolean
    /** 允许进入的角色；不写表示任意已登录角色都能进 */
    roles?: UserRole[]
  }
}

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
      meta: { title: '发现' },
    },
    {
      path: '/resources',
      name: 'resources',
      component: () => import('../pages/ResourceCenterPage.vue'),
      meta: { title: '资源中心', requiresAuth: true },
    },
    {
      path: '/my-submissions',
      name: 'my-submissions',
      component: () => import('../pages/StudentSubmissionsPage.vue'),
      meta: { title: '我的投稿', requiresAuth: true, roles: ['student'] },
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('../pages/FavoritesPage.vue'),
      meta: { title: '我的收藏', requiresAuth: true },
    },
    {
      path: '/learning',
      name: 'learning',
      component: () => import('../pages/LearningProgressPage.vue'),
      meta: { title: '学习进度', requiresAuth: true },
    },
    {
      path: '/teacher',
      name: 'teacher',
      component: () => import('../pages/TeacherWorkbenchPage.vue'),
      meta: { title: '教师工作台', requiresAuth: true, roles: ['teacher'] },
    },
    {
      path: '/teacher/courses',
      name: 'teacher-courses',
      component: () => import('../pages/CourseManagePage.vue'),
      meta: { title: '我的课程', requiresAuth: true, roles: ['teacher'] },
    },
    {
      path: '/teacher/resources',
      name: 'teacher-resources',
      component: () => import('../pages/TeacherResourceListPage.vue'),
      meta: { title: '我的资源', requiresAuth: true, roles: ['teacher'] },
    },
    {
      path: '/teacher/reviews',
      name: 'teacher-reviews',
      component: () => import('../pages/ReviewQueuePage.vue'),
      meta: { title: '课程审核', requiresAuth: true, roles: ['teacher'] },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../pages/AdminOverviewPage.vue'),
      meta: { title: '首页概览', requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('../pages/AdminUsersPage.vue'),
      meta: { title: '用户管理', requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/categories',
      name: 'admin-categories',
      component: () => import('../pages/AdminCategoriesPage.vue'),
      meta: { title: '分类管理', requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/courses',
      name: 'admin-courses',
      component: () => import('../pages/CourseManagePage.vue'),
      meta: { title: '课程管理', requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/reviews',
      name: 'admin-reviews',
      component: () => import('../pages/ReviewQueuePage.vue'),
      meta: { title: '资源审核', requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/operation-logs',
      name: 'admin-operation-logs',
      component: () => import('../pages/AdminOperationLogsPage.vue'),
      meta: { title: '操作日志' },
    },
    {
      path: '/admin/resources',
      name: 'admin-resources',
      component: () => import('../pages/AdminResourceListPage.vue'),
      meta: { title: '资源管理', requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/LoginPage.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../pages/RegisterPage.vue'),
      meta: { title: '注册' },
    }
  ],
})

/*
 * 路由守卫。
 *
 * 会话只存在内存里（见 api/session.ts），刷新即登出是文档规定的设计
 * （architecture.md:50、ui-design-spec.md:182 明确不得持久化令牌），
 * 所以这里不需要异步恢复会话、也不请求 /users/me——纯同步判断就够。
 * setSession 同时写入令牌和用户，不存在"有令牌没用户"的中间态。
 */
router.beforeEach((to) => {
  const { isLoggedIn, currentUser } = useSession()
  const role = currentUser.value?.role

  // ① 需要登录但没有会话 → 去登录页，带上回来的路（登录后可回到原页）
  if (to.meta.requiresAuth && !isLoggedIn.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // ② 角色不符 → 回自己的落地页。不能去 /login：用户已经登录了，
  //    再让他"重新登录"只会让人以为账号出了问题。
  if (to.meta.roles && role && !to.meta.roles.includes(role)) {
    return homeForRole(role)
  }

  // ③ 已登录还访问登录/注册页 → 送回自己的落地页
  if ((to.name === 'login' || to.name === 'register') && isLoggedIn.value && role) {
    return homeForRole(role)
  }

  return true
})
