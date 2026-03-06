import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import DigestView from '../views/DigestView.vue';

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
  ],
});

export default router;
