<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  NAlert,
  NButton,
  NDivider,
  NEmpty,
  NIcon,
  NInput,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NSlider,
  NSpin,
  NStatistic,
  useMessage,
} from 'naive-ui';
import type { SelectOption } from 'naive-ui';
import {
  ArrowBackOutline,
  FilterOutline,
  SearchOutline,
  TimeOutline,
  TrendingUpOutline,
} from '@vicons/ionicons5';
import ArticleCard from '../components/ArticleCard.vue';
import { useDigestStore } from '../stores/digest';
import type { QueryParams } from '../types';

const props = defineProps<{
  date: string;
}>();

const store = useDigestStore();
const router = useRouter();
const message = useMessage();

const searchKeyword = ref('');
const selectedCategory = ref<string | null>(null);
const selectedTags = ref<string[]>([]);
const minImportance = ref(1);
const sortBy = ref<'importance' | 'published'>('importance');

const categories: SelectOption[] = [
  { label: 'All', value: '' },
  { label: 'Arxiv papers', value: 'arxiv' },
  { label: 'Official updates', value: 'official' },
  { label: 'News coverage', value: 'news' },
  { label: 'Community', value: 'community' },
];

const loadData = () => {
  const params: QueryParams = {
    q: searchKeyword.value || undefined,
    category: selectedCategory.value || undefined,
    tags: selectedTags.value.length > 0 ? selectedTags.value : undefined,
    min_importance: minImportance.value,
    sort: sortBy.value,
  };
  void store.fetchDigest(props.date, params);
};

let loadTimer: ReturnType<typeof setTimeout> | null = null;

const cancelScheduledLoad = () => {
  if (loadTimer !== null) {
    clearTimeout(loadTimer);
    loadTimer = null;
  }
};

const scheduleLoad = (delay = 300) => {
  cancelScheduledLoad();
  loadTimer = window.setTimeout(() => {
    loadTimer = null;
    loadData();
  }, delay);
};

watch([searchKeyword, selectedCategory, selectedTags, minImportance, sortBy], () => {
  scheduleLoad();
});

watch(
  () => props.date,
  () => {
    store.clearTagCache();
    cancelScheduledLoad();
    loadData();
  },
);

watch(
  () => store.error,
  (error) => {
    if (error) {
      message.error(error);
    }
  },
);

const tagOptions = computed(() => {
  const tags =
    store.allTagsDate === props.date && store.allTags.length > 0
      ? store.allTags
      : Object.keys(store.currentDigest?.stats?.by_tag ?? {});
  return tags.map((tag) => ({
    label: tag,
    value: tag,
  }));
});

const goBack = () => {
  router.push('/');
};

const siderContentRef = ref<HTMLElement | null>(null);
const prefersReducedMotion = ref(false);
let mediaQuery: MediaQueryList | null = null;
let removeMotionListener: (() => void) | null = null;
let currentY = 0;
let velocityY = 0;
let targetY = 0;
let rafId = 0;
let siderInitialTop = 0;
const STIFFNESS = 0.08;
const DAMPING = 0.82;
const REST_THRESHOLD = 0.5;
let isAnimating = false;

const updateReducedMotion = (value: boolean) => {
  prefersReducedMotion.value = value;
};

const clampTarget = () => {
  const el = siderContentRef.value;
  if (!el) return 0;
  const aside = el.parentElement;
  if (!aside) return 0;
  const maxTravel = aside.offsetHeight - el.offsetHeight;
  const scrollOffset = Math.max(0, window.scrollY - siderInitialTop + 24);
  return Math.min(scrollOffset, Math.max(0, maxTravel));
};

const applySidebarPosition = (y: number) => {
  if (siderContentRef.value) {
    siderContentRef.value.style.transform = `translateY(${y}px)`;
  }
};

const animate = () => {
  const force = (targetY - currentY) * STIFFNESS;
  velocityY += force;
  velocityY *= DAMPING;
  currentY += velocityY;
  applySidebarPosition(currentY);

  if (Math.abs(velocityY) < REST_THRESHOLD && Math.abs(targetY - currentY) < REST_THRESHOLD) {
    currentY = targetY;
    applySidebarPosition(currentY);
    isAnimating = false;
    return;
  }

  rafId = requestAnimationFrame(animate);
};

const onScroll = () => {
  targetY = clampTarget();
  if (prefersReducedMotion.value) {
    currentY = targetY;
    velocityY = 0;
    applySidebarPosition(currentY);
    return;
  }

  if (!isAnimating) {
    isAnimating = true;
    rafId = requestAnimationFrame(animate);
  }
};

onMounted(() => {
  store.clearTagCache();
  loadData();

  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  updateReducedMotion(mediaQuery.matches);

  const handleMotionChange = (event: MediaQueryListEvent) => {
    updateReducedMotion(event.matches);
  };

  mediaQuery.addEventListener('change', handleMotionChange);
  removeMotionListener = () => mediaQuery?.removeEventListener('change', handleMotionChange);

  nextTick(() => {
    if (siderContentRef.value) {
      siderInitialTop = siderContentRef.value.getBoundingClientRect().top + window.scrollY;
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  });
});

onBeforeUnmount(() => {
  cancelScheduledLoad();
  removeMotionListener?.();
  window.removeEventListener('scroll', onScroll);
  cancelAnimationFrame(rafId);
});
</script>

<template>
  <div class="digest-view">
    <div class="header-nav animate-fade-up">
      <n-button text @click="goBack" class="back-btn">
        <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        Back to archive
      </n-button>
      <div class="current-date">
        <h2>AI Daily - {{ date }}</h2>
        <span v-if="store.currentDigest" class="gen-time">
          Generated {{ new Date(store.currentDigest.generated_at).toLocaleString() }}
        </span>
      </div>
    </div>

    <div class="main-layout">
      <aside class="filter-sider animate-fade-up delay-1">
        <div ref="siderContentRef" class="sider-content">
          <div class="filter-section">
            <h3 class="filter-title"><n-icon><SearchOutline /></n-icon> Search</h3>
            <n-input v-model:value="searchKeyword" placeholder="Search title or summary..." clearable />
          </div>

          <n-divider />

          <div class="filter-section">
            <h3 class="filter-title"><n-icon><FilterOutline /></n-icon> Filters</h3>

            <div class="filter-item">
              <label>Category</label>
              <n-select v-model:value="selectedCategory" :options="categories" placeholder="Choose a category" />
            </div>

            <div class="filter-item">
              <label>Tags</label>
              <n-select v-model:value="selectedTags" :options="tagOptions" multiple placeholder="Choose tags" />
            </div>

            <div class="filter-item">
              <label>Minimum importance ({{ minImportance }}+)</label>
              <n-slider v-model:value="minImportance" :min="1" :max="5" :step="1" />
            </div>
          </div>

          <n-divider />

          <div class="filter-section">
            <h3 class="filter-title">Sort</h3>
            <n-radio-group v-model:value="sortBy" size="small" class="sort-group">
              <n-radio-button value="importance">
                <n-icon><TrendingUpOutline /></n-icon> Importance
              </n-radio-button>
              <n-radio-button value="published">
                <n-icon><TimeOutline /></n-icon> Published
              </n-radio-button>
            </n-radio-group>
          </div>

          <div class="stats-card" v-if="store.currentDigest?.stats">
            <n-statistic label="Visible results" :value="store.currentDigest.stats.total">
              <template #suffix>items</template>
            </n-statistic>
          </div>
        </div>
      </aside>

      <main class="content-area">
        <n-alert
          v-if="store.error"
          type="error"
          title="Digest request failed"
          class="error-alert animate-fade-up"
        >
          {{ store.error }}
        </n-alert>
        <n-spin :show="store.loading">
          <div v-if="store.currentDigest?.articles.length" class="article-list animate-fade-up delay-2">
            <article-card
              v-for="(article, index) in store.currentDigest.articles"
              :key="article.id"
              :article="article"
              :style="{ animationDelay: `${index * 50 + 200}ms` }"
            />
          </div>
          <n-empty
            v-else-if="!store.loading"
            description="No articles match the current filters."
            class="empty-state animate-fade-up"
          />
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
  margin-bottom: 40px;
}

.back-btn {
  font-size: 15px;
  color: var(--n-text-color-3);
  transition: color 0.2s;
}

.back-btn:hover {
  color: var(--n-text-color);
}

.current-date h2 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 32px;
  font-weight: 500;
  color: var(--n-text-color);
  letter-spacing: -0.01em;
}

.gen-time {
  font-size: 13px;
  color: var(--n-text-color-3);
  letter-spacing: 0.02em;
}

.main-layout {
  display: flex;
  align-items: stretch;
  gap: 40px;
}

.filter-sider {
  width: 280px;
  flex-shrink: 0;
}

.sider-content {
  padding: 24px;
  background-color: var(--n-card-color);
  border: 1px solid var(--n-border-color);
  border-radius: 16px;
  will-change: transform;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03), 0 1px 4px rgba(0, 0, 0, 0.02);
}

.is-dark .sider-content {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2), 0 1px 4px rgba(0, 0, 0, 0.1);
}

.filter-section {
  margin-bottom: 24px;
}

.filter-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--n-text-color-3);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.filter-item {
  margin-bottom: 20px;
}

.filter-item label {
  display: block;
  font-size: 13px;
  color: var(--n-text-color-2);
  margin-bottom: 8px;
  font-weight: 500;
}

.sort-group {
  width: 100%;
}

:deep(.n-radio-button) {
  flex: 1;
  text-align: center;
}

.stats-card {
  margin-top: 32px;
  padding: 20px;
  background-color: var(--n-body-color);
  border: 1px solid var(--n-border-color);
  border-radius: 12px;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.error-alert {
  margin-bottom: 16px;
}

.empty-state {
  margin-top: 100px;
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
