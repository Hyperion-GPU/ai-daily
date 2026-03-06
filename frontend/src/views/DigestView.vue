<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useDigestStore } from '../stores/digest';
import {
  NSelect, NSlider,
  NInput, NRadioGroup, NRadioButton, NStatistic,
  NEmpty, NSpin, NButton, NIcon, NDivider
} from 'naive-ui';
import type { SelectOption } from 'naive-ui';
import { FilterOutline, SearchOutline, ArrowBackOutline, TrendingUpOutline, TimeOutline } from '@vicons/ionicons5';
import ArticleCard from '../components/ArticleCard.vue';
import type { QueryParams } from '../types';

const props = defineProps<{
  date: string;
}>();

const store = useDigestStore();
const router = useRouter();

// Filters
const searchKeyword = ref('');
const selectedCategory = ref<string | null>(null);
const selectedTags = ref<string[]>([]);
const minImportance = ref(1);
const sortBy = ref<'importance' | 'published'>('importance');

// Category options
const categories: SelectOption[] = [
  { label: '全部', value: '' },
  { label: 'Arxiv 研究', value: 'arxiv' },
  { label: '官方发布', value: 'official' },
  { label: '业界新闻', value: 'news' },
  { label: '社区动态', value: 'community' },
];

const loadData = () => {
  const params: QueryParams = {
    q: searchKeyword.value || undefined,
    category: selectedCategory.value || undefined,
    tags: selectedTags.value.length > 0 ? selectedTags.value : undefined,
    min_importance: minImportance.value,
    sort: sortBy.value,
  };
  store.fetchDigest(props.date, params);
};

onMounted(loadData);

watch([searchKeyword, selectedCategory, selectedTags, minImportance, sortBy], () => {
  loadData();
});

watch(() => props.date, loadData);

const tagOptions = computed(() => {
  if (!store.currentDigest?.stats?.by_tag) return [];
  return Object.keys(store.currentDigest.stats.by_tag).map(tag => ({
    label: tag,
    value: tag
  }));
});

const goBack = () => {
  router.push('/');
};

// --- Spring physics scroll-following sidebar ---
const siderContentRef = ref<HTMLElement | null>(null);
let currentY = 0;
let velocityY = 0;
let targetY = 0;
let rafId = 0;
let siderInitialTop = 0;
const STIFFNESS = 0.08;
const DAMPING = 0.82;
const REST_THRESHOLD = 0.5;
let isAnimating = false;

const clampTarget = () => {
  const el = siderContentRef.value;
  if (!el) return 0;
  const aside = el.parentElement;
  if (!aside) return 0;
  // How far sidebar can travel inside the aside
  const maxTravel = aside.offsetHeight - el.offsetHeight;
  const scrollOffset = Math.max(0, window.scrollY - siderInitialTop + 24);
  return Math.min(scrollOffset, Math.max(0, maxTravel));
};

const animate = () => {
  const force = (targetY - currentY) * STIFFNESS;
  velocityY += force;
  velocityY *= DAMPING;
  currentY += velocityY;

  if (siderContentRef.value) {
    siderContentRef.value.style.transform = `translateY(${currentY}px)`;
  }

  if (Math.abs(velocityY) < REST_THRESHOLD && Math.abs(targetY - currentY) < REST_THRESHOLD) {
    currentY = targetY;
    if (siderContentRef.value) {
      siderContentRef.value.style.transform = `translateY(${currentY}px)`;
    }
    isAnimating = false;
    return;
  }

  rafId = requestAnimationFrame(animate);
};

const onScroll = () => {
  targetY = clampTarget();
  if (!isAnimating) {
    isAnimating = true;
    rafId = requestAnimationFrame(animate);
  }
};

onMounted(() => {
  nextTick(() => {
    if (siderContentRef.value) {
      siderInitialTop = siderContentRef.value.getBoundingClientRect().top + window.scrollY;
    }
    window.addEventListener('scroll', onScroll, { passive: true });
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll);
  cancelAnimationFrame(rafId);
});
</script>

<template>
  <div class="digest-view">
    <div class="header-nav">
      <n-button text @click="goBack" class="back-btn">
        <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        返回列表
      </n-button>
      <div class="current-date">
        <h2>AI Daily — {{ date }}</h2>
        <span v-if="store.currentDigest" class="gen-time">生成于 {{ new Date(store.currentDigest.generated_at).toLocaleString() }}</span>
      </div>
    </div>

    <div class="main-layout">
      <!-- Sidebar -->
      <aside class="filter-sider">
        <div ref="siderContentRef" class="sider-content">
          <div class="filter-section">
            <h3 class="filter-title"><n-icon><SearchOutline /></n-icon> 搜索</h3>
            <n-input v-model:value="searchKeyword" placeholder="搜索标题或摘要..." clearable />
          </div>

          <n-divider />

          <div class="filter-section">
            <h3 class="filter-title"><n-icon><FilterOutline /></n-icon> 筛选</h3>

            <div class="filter-item">
              <label>内容分类</label>
              <n-select v-model:value="selectedCategory" :options="categories" placeholder="选择分类" />
            </div>

            <div class="filter-item">
              <label>热门标签</label>
              <n-select v-model:value="selectedTags" :options="tagOptions" multiple placeholder="选择标签" />
            </div>

            <div class="filter-item">
              <label>最低重要性 ({{ minImportance }}+)</label>
              <n-slider v-model:value="minImportance" :min="1" :max="5" :step="1" />
            </div>
          </div>

          <n-divider />

          <div class="filter-section">
            <h3 class="filter-title">排序方式</h3>
            <n-radio-group v-model:value="sortBy" size="small" class="sort-group">
              <n-radio-button value="importance">
                <n-icon><TrendingUpOutline /></n-icon> 重要性
              </n-radio-button>
              <n-radio-button value="published">
                <n-icon><TimeOutline /></n-icon> 时间
              </n-radio-button>
            </n-radio-group>
          </div>

          <div class="stats-card" v-if="store.currentDigest?.stats">
            <n-statistic label="今日资讯" :value="store.currentDigest.stats.total">
              <template #suffix>篇</template>
            </n-statistic>
          </div>
        </div>
      </aside>

      <!-- Content -->
      <main class="content-area">
        <n-spin :show="store.loading">
          <div v-if="store.currentDigest?.articles.length" class="article-list">
            <article-card
              v-for="article in store.currentDigest.articles"
              :key="article.id"
              :article="article"
            />
          </div>
          <n-empty v-else-if="!store.loading" description="没有找到符合条件的资讯" class="empty-state" />
        </n-spin>
      </main>
    </div>
  </div>
</template>

<style scoped>
.digest-view {
  display: flex;
  flex-direction: column;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
}

.current-date h2 {
  margin: 0;
  font-size: 24px;
  color: #f0f6fc;
}

.gen-time {
  font-size: 12px;
  color: #8b949e;
}

.main-layout {
  display: flex;
  align-items: stretch;
  gap: 24px;
}

.filter-sider {
  width: 280px;
  flex-shrink: 0;
}

.sider-content {
  padding: 16px;
  background-color: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  will-change: transform;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-title {
  font-size: 14px;
  font-weight: 600;
  color: #8b949e;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
}

.filter-item {
  margin-bottom: 16px;
}

.filter-item label {
  display: block;
  font-size: 13px;
  color: #c9d1d9;
  margin-bottom: 8px;
}

.sort-group {
  width: 100%;
}

:deep(.n-radio-button) {
  flex: 1;
  text-align: center;
}

.stats-card {
  margin-top: 24px;
  padding: 16px;
  background-color: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.empty-state {
  margin-top: 80px;
}

@media (max-width: 900px) {
  .main-layout {
    flex-direction: column;
  }
  .filter-sider {
    width: 100%;
  }
}
</style>
