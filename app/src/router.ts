import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('./views/HomeView.vue'),
    },
    {
      path: '/audit/:slug',
      component: () => import('./views/AuditPage.vue'),
    },
  ],
})

export default router
