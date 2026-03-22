import { createRouter, createWebHistory } from 'vue-router';

const HomeView = () => import('../views/HomeView.vue');
const DigestView = () => import('../views/DigestView.vue');
const GithubTrendingView = () => import('../views/GithubTrendingView.vue');

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/digest/:date',
      name: 'digest',
      component: DigestView,
      props: true,
    },
    {
      path: '/github',
      name: 'github_trending_latest',
      component: GithubTrendingView,
    },
    {
      path: '/github/:date',
      name: 'github_trending_date',
      component: GithubTrendingView,
      props: true,
    },
  ],
});

export default router;
