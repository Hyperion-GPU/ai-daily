<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  NAlert,
  NButton,
  NEmpty,
  NIcon,
  NInput,
  NSelect,
  NSlider,
  NSpin,
  useMessage,
} from 'naive-ui';
import { RefreshOutline, SearchOutline } from '@vicons/ionicons5';
import { GITHUB_FETCH_ALREADY_RUNNING, useGithubStore } from '../stores/github';
import { useLocale } from '../composables/useLocale';
import ProjectCard from '../components/ProjectCard.vue';
import FetchProgressCard from '../components/FetchProgressCard.vue';
import type { GitHubFetchStatus, GitHubQueryParams } from '../types';

const route = useRoute();
const store = useGithubStore();
const { copy, dateTimeLocale } = useLocale();
const message = useMessage();
const hasInitialized = ref(false);

const activeDate = computed(() => {
  const routeDate = typeof route.params.date === 'string' ? route.params.date : '';
  return routeDate || store.dateList.latest || '';
});

const searchQuery = ref('');
const selectedCategory = ref('');
const selectedLanguages = ref<string[]>([]);
const minStars = ref(0);
const selectedTrend = ref<'' | 'hot' | 'rising' | 'stable'>('');
const sortBy = ref<'stars' | 'stars_today' | 'stars_weekly' | 'updated'>('stars');

const categoryOptions = computed(() => [
  { label: copy.value.github.categoryAll, value: '' },
  { label: copy.value.github.categoryLLM, value: 'llm' },
  { label: copy.value.github.categoryAgent, value: 'agent' },
  { label: copy.value.github.categoryCV, value: 'cv' },
  { label: copy.value.github.categoryNLP, value: 'nlp' },
  { label: copy.value.github.categoryFramework, value: 'ml_framework' },
  { label: copy.value.github.categoryMLOps, value: 'mlops' },
  { label: copy.value.github.categoryGeneral, value: 'general' },
]);

const trendOptions = computed(() => [
  { label: copy.value.github.trendAll, value: '' as const },
  { label: copy.value.github.trendHot, value: 'hot' as const },
  { label: copy.value.github.trendRising, value: 'rising' as const },
  { label: copy.value.github.trendStable, value: 'stable' as const },
]);

const sortOptions = computed(() => [
  { label: copy.value.github.sortStars, value: 'stars' as const },
  { label: copy.value.github.sortStarsToday, value: 'stars_today' as const },
  { label: copy.value.github.sortStarsWeekly, value: 'stars_weekly' as const },
  { label: copy.value.github.sortUpdated, value: 'updated' as const },
]);

const languageOptions = computed(() => {
  const byLanguage = store.currentTrending?.stats?.by_language ?? {};
  return Object.entries(byLanguage)
    .sort((a, b) => b[1] - a[1])
    .map(([lang, count]) => ({
      label: `${lang} (${count})`,
      value: lang,
    }));
});

const queryParams = computed<GitHubQueryParams>(() => ({
  q: searchQuery.value.trim() || null,
  category: selectedCategory.value || null,
  language: selectedLanguages.value.length > 0 ? [...selectedLanguages.value] : null,
  min_stars: minStars.value,
  trend: selectedTrend.value || null,
  sort: sortBy.value,
}));

const fetchProjects = debounce(() => {
  void store.fetchTrending(activeDate.value, queryParams.value);
}, 260);

const refreshTrendingData = async () => {
  await store.fetchTrending(activeDate.value, queryParams.value);
};

const handleFetchSettled = async (finalStatus: GitHubFetchStatus) => {
  await refreshTrendingData();

  if (finalStatus.last_outcome === 'success') {
    message.success(copy.value.github.fetchSuccess);
    return;
  }

  if (finalStatus.last_outcome === 'error') {
    message.error(finalStatus.error || copy.value.github.fetchError);
  }
};

const initializeView = async () => {
  await store.fetchDateList();
  await refreshTrendingData();
  hasInitialized.value = true;

  const status = await store.refreshFetchStatus();
  if (status.running) {
    store.startFetchPolling(handleFetchSettled);
  }
};

watch(
  [activeDate, queryParams],
  () => {
    if (!hasInitialized.value) {
      return;
    }
    fetchProjects();
  },
  { deep: true },
);

onMounted(() => {
  void initializeView();
});

onBeforeUnmount(() => {
  store.stopFetchPolling();
});

const onFetchLatest = async () => {
  if (store.fetchStatus.running) {
    message.warning(copy.value.github.fetchAlreadyRunning);
    return;
  }

  try {
    await store.triggerFetch();
    store.startFetchPolling(handleFetchSettled);
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : copy.value.github.fetchError;
    if (errorMessage === GITHUB_FETCH_ALREADY_RUNNING) {
      message.warning(copy.value.github.fetchAlreadyRunning);
      store.startFetchPolling(handleFetchSettled);
      return;
    }
    message.error(errorMessage);
  }
};

const visibleCount = computed(() => store.currentTrending?.projects?.length ?? 0);
const languageCount = computed(() => Object.keys(store.currentTrending?.stats?.by_language ?? {}).length);

const sortLabel = computed(() => {
  switch (sortBy.value) {
    case 'stars_today':
      return copy.value.github.sortStarsToday;
    case 'stars_weekly':
      return copy.value.github.sortStarsWeekly;
    case 'updated':
      return copy.value.github.sortUpdated;
    default:
      return copy.value.github.sortStars;
  }
});

const trendLabel = computed(() => {
  switch (selectedTrend.value) {
    case 'hot':
      return copy.value.github.trendHot;
    case 'rising':
      return copy.value.github.trendRising;
    case 'stable':
      return copy.value.github.trendStable;
    default:
      return copy.value.github.trendAll;
  }
});

const activeFilterChips = computed(() => {
  const chips: string[] = [];

  if (searchQuery.value.trim()) {
    chips.push(`${copy.value.github.search}: ${searchQuery.value.trim()}`);
  }

  if (selectedCategory.value) {
    const categoryLabel = categoryOptions.value.find((option) => option.value === selectedCategory.value)?.label;
    if (categoryLabel) {
      chips.push(categoryLabel);
    }
  }

  if (selectedLanguages.value.length > 0) {
    chips.push(selectedLanguages.value.slice(0, 3).join(' · '));
  }

  if (minStars.value > 0) {
    chips.push(`${copy.value.github.minStars}: ${minStars.value}`);
  }

  chips.push(`${copy.value.github.trend}: ${trendLabel.value}`);
  chips.push(`${copy.value.github.sort}: ${sortLabel.value}`);
  return chips;
});

const snapshotLabel = computed(() => {
  const raw = store.currentTrending?.generated_at;
  if (!raw) {
    return activeDate.value || '—';
  }
  return new Intl.DateTimeFormat(dateTimeLocale.value, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(raw));
});

const recentDates = computed(() => store.dateList.dates.slice(0, 6));

function debounce(fn: (...args: unknown[]) => void, ms = 300) {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: unknown[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), ms);
  };
}
</script>

<template>
  <div class="github-view">
    <section class="paper-panel github-hero animate-fade-up">
      <div class="github-hero__header">
        <div class="github-hero__copy">
          <p class="eyebrow">{{ copy.app.githubNav }}</p>
          <h1 class="editorial-title">{{ copy.github.pageTitle }}</h1>
          <p class="lede">{{ copy.github.pageDescription }}</p>
        </div>

        <div class="github-hero__actions">
          <n-button
            type="primary"
            size="large"
            class="fetch-button"
            :loading="store.fetchStatus.running"
            @click="onFetchLatest"
          >
            <template #icon>
              <n-icon>
                <RefreshOutline />
              </n-icon>
            </template>
            {{ store.fetchStatus.running ? copy.github.fetchRunning : copy.github.fetchData }}
          </n-button>
          <span class="soft-pill">{{ snapshotLabel }}</span>
        </div>
      </div>

      <div class="github-hero__footer">
        <div class="metric-grid github-metrics">
          <div class="metric-card">
            <span class="metric-value">{{ visibleCount }}</span>
            <span class="metric-label">{{ copy.github.visibleResults }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{{ languageCount }}</span>
            <span class="metric-label">{{ copy.github.language }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{{ store.currentTrending?.date ?? activeDate }}</span>
            <span class="metric-label">{{ copy.home.latest }}</span>
          </div>
        </div>

        <div class="chip-row">
          <router-link
            v-for="date in recentDates"
            :key="date"
            :to="{ name: 'github_trending_date', params: { date } }"
            class="date-link"
            :class="{ 'date-link--active': date === (store.currentTrending?.date ?? activeDate) }"
          >
            {{ date }}
          </router-link>
        </div>
      </div>
    </section>

    <FetchProgressCard
      :running="store.fetchStatus.running"
      :progress="store.fetchStatus.progress"
      :error="store.fetchStatus.error"
      class="animate-fade-up delay-1"
    />

    <div class="github-layout">
      <aside class="paper-panel filters-panel animate-fade-up delay-1">
        <div class="filter-rail__header">
          <p class="eyebrow">{{ copy.digest.filters }}</p>
          <h2 class="section-title">{{ copy.github.search }}</h2>
        </div>

        <div class="filter-stack">
          <div>
            <label class="field-label">{{ copy.github.search }}</label>
            <n-input v-model:value="searchQuery" :placeholder="copy.github.searchPlaceholder" clearable>
              <template #prefix>
                <n-icon>
                  <SearchOutline />
                </n-icon>
              </template>
            </n-input>
          </div>

          <div>
            <label class="field-label">{{ copy.github.category }}</label>
            <n-select
              v-model:value="selectedCategory"
              :options="categoryOptions"
              :placeholder="copy.github.categoryAll"
              clearable
            />
          </div>

          <div>
            <label class="field-label">{{ copy.github.language }}</label>
            <n-select
              v-model:value="selectedLanguages"
              multiple
              clearable
              filterable
              :options="languageOptions"
              :placeholder="copy.github.language"
            />
          </div>

          <div>
            <label class="field-label">{{ copy.github.minStars }} · {{ minStars }}</label>
            <n-slider v-model:value="minStars" :min="0" :max="10000" :step="100" />
          </div>

          <div>
            <label class="field-label">{{ copy.github.trend }}</label>
            <div class="filter-option-grid">
              <button
                v-for="option in trendOptions"
                :key="option.value || 'all'"
                type="button"
                class="filter-option"
                :class="{ 'filter-option--active': selectedTrend === option.value }"
                @click="selectedTrend = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <div>
            <label class="field-label">{{ copy.github.sort }}</label>
            <div class="filter-option-grid">
              <button
                v-for="option in sortOptions"
                :key="option.value"
                type="button"
                class="filter-option"
                :class="{ 'filter-option--active': sortBy === option.value }"
                @click="sortBy = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
        </div>
      </aside>

      <section class="projects-column">
        <n-alert
          v-if="store.error"
          type="error"
          class="request-alert"
          :title="copy.github.fetchError"
        >
          {{ store.error }}
        </n-alert>

        <div class="paper-panel results-summary animate-fade-up delay-2">
          <div>
            <p class="eyebrow">{{ copy.github.visibleResults }}</p>
            <h2 class="section-title">
              {{ visibleCount }} {{ copy.github.items }}
            </h2>
          </div>

          <div class="chip-row">
            <span v-for="chip in activeFilterChips" :key="chip" class="soft-pill">
              {{ chip }}
            </span>
          </div>
        </div>

        <n-spin :show="store.loading && !store.currentTrending">
          <div v-if="store.currentTrending?.projects?.length" class="project-stack">
            <ProjectCard
              v-for="(project, index) in store.currentTrending.projects"
              :key="project.id"
              :project="project"
              class="animate-fade-up"
              :style="{ animationDelay: `${Math.min(index * 35, 280) + 140}ms` }"
            />
          </div>

          <div v-else-if="!store.loading" class="paper-panel empty-panel">
            <n-empty :description="copy.github.empty" />
          </div>
        </n-spin>
      </section>
    </div>
  </div>
</template>

<style scoped>
.github-view {
  display: grid;
  gap: 24px;
}

.github-hero,
.filters-panel,
.results-summary,
.empty-panel {
  padding: 30px;
}

.github-hero {
  display: grid;
  gap: 24px;
}

.github-hero__header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  align-items: start;
}

.github-hero__copy {
  display: grid;
  gap: 14px;
}

.github-hero__actions {
  display: grid;
  justify-items: end;
  gap: 12px;
}

.fetch-button {
  min-width: 212px;
}

.github-hero__footer {
  display: grid;
  gap: 18px;
}

.date-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid rgba(73, 58, 45, 0.1);
  background: rgba(255, 252, 247, 0.78);
  text-decoration: none;
  color: var(--ink-soft);
  font-size: 0.88rem;
}

.date-link--active,
.date-link:hover {
  color: var(--ink-strong);
  background: rgba(127, 102, 83, 0.1);
}

.github-layout {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.filters-panel {
  position: sticky;
  top: 98px;
  display: grid;
  gap: 22px;
  min-width: 0;
}

.filter-rail__header {
  display: grid;
  gap: 8px;
}

.filter-stack,
.filter-stack > div {
  min-width: 0;
}

.filters-panel :deep(.n-input),
.filters-panel :deep(.n-base-selection),
.filters-panel :deep(.n-slider) {
  width: 100%;
  max-width: 100%;
}

.filters-panel :deep(.n-input-wrapper),
.filters-panel :deep(.n-base-selection-label),
.filters-panel :deep(.n-base-selection-tags) {
  max-width: 100%;
}

.filter-option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.filter-option {
  width: 100%;
  min-width: 0;
  padding: 11px 14px;
  border-radius: 14px;
  border: 1px solid rgba(73, 58, 45, 0.12);
  background: rgba(255, 252, 247, 0.78);
  color: var(--ink-soft);
  font: inherit;
  line-height: 1.25;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.filter-option:hover {
  color: var(--ink-strong);
  border-color: rgba(73, 58, 45, 0.2);
}

.filter-option--active {
  background: rgba(127, 102, 83, 0.1);
  border-color: rgba(127, 102, 83, 0.32);
  color: var(--ink-strong);
}

.projects-column {
  display: grid;
  gap: 20px;
}

.request-alert {
  border-radius: 18px;
}

.results-summary {
  display: grid;
  gap: 18px;
}

.project-stack {
  display: grid;
  gap: 18px;
}

@media (max-width: 1024px) {
  .github-hero__header,
  .github-layout {
    grid-template-columns: 1fr;
  }

  .github-hero__actions {
    justify-items: start;
  }

  .filters-panel {
    position: static;
  }
}

@media (max-width: 640px) {
  .github-hero,
  .filters-panel,
  .results-summary,
  .empty-panel {
    padding: 22px;
  }

  .fetch-button {
    width: 100%;
  }

  .filter-option-grid {
    grid-template-columns: 1fr;
  }
}
</style>
