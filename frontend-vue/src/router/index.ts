/**
 * 路由配置。页面组件采用懒加载（路由级代码分割）。
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/chat' },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { title: 'RAG 问答', icon: 'ChatDotRound' },
  },
  {
    path: '/kb',
    name: 'kb',
    component: () => import('@/views/KbView.vue'),
    meta: { title: '知识库管理', icon: 'FolderOpened' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = `${(to.meta.title as string) || ''} · 私有知识库 RAG`
})

export default router
