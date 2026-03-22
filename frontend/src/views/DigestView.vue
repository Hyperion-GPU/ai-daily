<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { LocationQuery, LocationQueryRaw } from 'vue-router';
import {
  NAlert,
  NButton,
  NEmpty,
  NIcon,
  NInput,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NSlider,
  NSpin,
  useMessage,
} from 'naive-ui';
import type { SelectOption } from 'naive-ui';
import { ArrowBackOutline, SearchOutline } from '@vicons/ionicons5';
import ArticleCard from '../components/ArticleCard.vue';
import { useLocale } from '../composables/useLocale';
import { useDigestStore } from '../stores/digest';
import type { QueryParams } from '../types';

const props = defineProps<{
  date: string;
}>();

const store = useDigestStore();
const route = useRoute();
const router = useRouter();
const message = useMessage();
const { copy, dateTimeLocale } = useLocale();

const searchKeyword = ref('');
const selectedCategory = ref<string | null>(null);
const selectedTags = ref<string[]>([]);
const minImportance = ref(1);
const sortBy = ref<'importance' | 'published'>('importance');

const categories = computed<SelectOption[]>(() => [
  { label: copy.value.categories.all, value: '' },
  { label: copy.value.categories.arxiv, value: 'arxiv' },
  { label: copy.value.categories.official, value: 'official' },
  { label: copy.value.categories.news, value: 'news' },
  { label: copy.value.categories.community, value: 'community' },
]);

type QueryScalar = string | number | null | undefined;
type QueryValue = QueryScalar | readonly QueryScalar[];

const firstQueryValue = (value: QueryValue) => (Array.isArray(value) ? value[0] : value);

const queryValueList = (value: QueryValue) => {
  const values = Array.isArray(value) ? value : value == null ? [] : [value];
  return values
    .map((item) => String(item).trim())
    .filter((item) => item.length > 0);
};

const syncStateFromRoute = (query: LocationQuery) => {
  const queryText = firstQueryValue(query.q);
  searchKeyword.value = typeof queryText === 'string' ? queryText : '';

  const queryCategory = firstQueryValue(query.category);
  selectedCategory.value = typeof queryCategory === 'string' && queryCategory ? queryCategory : null;

  selectedTags.value = queryValueList(query.tags);

  const queryMinImportance = firstQueryValue(query.min_importance);
  const parsedImportance =
    typeof queryMinImportance === 'string' ? Number.parseInt(queryMinImportance, 10) : Number.NaN;
  minImportance.value =
    Number.isInteger(parsedImportance) && parsedImportance >= 1 && parsedImportance <= 5
      ? parsedImportance
      : 1;

  const querySort = firstQueryValue(query.sort);
  sortBy.value = querySort === 'published' ? 'published' : 'importance';
};

const buildQueryFromState = (): LocationQueryRaw => {
  const query: LocationQueryRaw = {};
  const normalizedKeyword = searchKeyword.value.trim();

  if (normalizedKeyword) {
    query.q = normalizedKeyword;
  }
  if (selectedCategory.value) {
    query.category = selectedCategory.value;
  }
  if (selectedTags.value.length > 0) {
    query.tags = [...selectedTags.value];
  }
  if (minImportance.value > 1) {
    query.min_importance = String(minImportance.value);
  }
  if (sortBy.value !== 'importance') {
    query.sort = sortBy.value;
  }

  return query;
};

const serializeQuery = (query: LocationQuery | LocationQueryRaw) =>
  Object.entries(query)
    .sort()
    .flatMap(([key, value]) => queryValueList(value).map((item) => `${key}=${item}`))
    .join('&');

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

let querySyncTimer: ReturnType<typeof setTimeout> | null = null;

const cancelScheduledQuerySync = () => {
  if (querySyncTimer !== null) {
    clearTimeout(querySyncTimer);
    querySyncTimer = null;
  }
};

const syncQueryToRoute = async () => {
  const nextQuery = buildQueryFromState();
  if (serializeQuery(route.query) === serializeQuery(nextQuery)) {
    return;
  }
  await router.replace({ query: nextQuery });
};

const scheduleQuerySync = (delay = 260) => {
  cancelScheduledQuerySync();
  querySyncTimer = window.setTimeout(() => {
    querySyncTimer = null;
    void syncQueryToRoute();
  }, delay);
};

watch([searchKeyword, selectedCategory, selectedTags, minImportance, sortBy], () => {
  scheduleQuerySync();
});

watch(
  () => route.query,
  (query) => {
    syncStateFromRoute(query);
    loadData();
  },
  { immediate: true },
);

watch(
  () => props.date,
  () => {
    store.clearTagCache();
    cancelScheduledQuerySync();
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

onMounted(() => {
  store.clearTagCache();
});

onBeforeUnmount(() => {
  cancelScheduledQuerySync();
});

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

const visibleCount = computed(() => store.currentDigest?.articles.length ?? 0);
const categoryCount = computed(() => Object.keys(store.currentDigest?.stats?.by_category ?? {}).length);
const tagCount = computed(() => Object.keys(store.currentDigest?.stats?.by_tag ?? {}).length);

const sortLabel = computed(() =>
  sortBy.value === 'published' ? copy.value.digest.published : copy.value.digest.importance,
);

const activeFilterChips = computed(() => {
  const chips: string[] = [];

  if (searchKeyword.value.trim()) {
    chips.push(`${copy.value.digest.search}: ${searchKeyword.value.trim()}`);
  }

  if (selectedCategory.value) {
    const categoryLabel = categories.value.find((option) => option.value === selectedCategory.value)?.label;
    if (typeof categoryLabel === 'string') {
      chips.push(categoryLabel);
    }
  }

  if (selectedTags.value.length > 0) {
    chips.push(selectedTags.value.slice(0, 3).map((tag) => `#${tag}`).join(' '));
  }

  if (minImportance.value > 1) {
    chips.push(`${copy.value.digest.importance} ≥ ${minImportance.value}`);
  }

  chips.push(`${copy.value.digest.sort}: ${sortLabel.value}`);
  return chips;
});

const generatedAtLabel = computed(() => {
  if (!store.currentDigest?.generated_at) {
    return null;
  }

  return new Intl.DateTimeFormat(dateTimeLocale.value, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(store.currentDigest.generated_at));
});

const goBack = () => {
  void router.push('/');
};
</script>

<template>
  <div class="digest-view">
    <section class="paper-panel digest-hero animate-fade-up">
      <div class="digest-hero__header">
        <n-button text class="back-button" @click="goBack">
          <template #icon>
            <n-icon>
              <ArrowBackOutline />
            </n-icon>
          </template>
          {{ copy.digest.backToArchive }}
        </n-button>
      </div>

      <div class="digest-hero__body">
        <div class="digest-hero__copy">
          <p class="eyebrow">{{ copy.app.digestNav }}</p>
          <h1 class="editorial-title">{{ date }}</h1>
          <p class="lede">
            <span class="muted">{{ copy.digest.generatedAt }}</span>
            <span>{{ generatedAtLabel ?? '—' }}</span>
          </p>
        </div>

        <div class="metric-grid digest-metrics">
          <div class="metric-card">
            <span class="metric-value">{{ visibleCount }}</span>
            <span class="metric-label">{{ copy.digest.visibleResults }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{{ categoryCount }}</span>
            <span class="metric-label">{{ copy.digest.category }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{{ tagCount }}</span>
            <span class="metric-label">{{ copy.digest.tags }}</span>
          </div>
        </div>
      </div>
    </section>

    <div class="digest-layout">
      <aside class="paper-panel filter-rail animate-fade-up delay-1">
        <div class="filter-rail__header">
          <p class="eyebrow">{{ copy.digest.filters }}</p>
          <h2 class="section-title">{{ copy.digest.search }}</h2>
        </div>

        <div class="filter-stack">
          <div>
            <label class="field-label">{{ copy.digest.search }}</label>
            <n-input v-model:value="searchKeyword" :placeholder="copy.digest.searchPlaceholder" clearable>
              <template #prefix>
                <n-icon>
                  <SearchOutline />
                </n-icon>
              </template>
            </n-input>
          </div>

          <div>
            <label class="field-label">{{ copy.digest.category }}</label>
            <n-select
              v-model:value="selectedCategory"
              :options="categories"
              :placeholder="copy.digest.categoryPlaceholder"
              clearable
            />
          </div>

          <div>
            <label class="field-label">{{ copy.digest.tags }}</label>
            <n-select
              v-model:value="selectedTags"
              multiple
              clearable
              filterable
              :options="tagOptions"
              :placeholder="copy.digest.tagsPlaceholder"
            />
          </div>

          <div>
            <label class="field-label">{{ copy.digest.minimumImportance }} · {{ minImportance }}</label>
            <n-slider v-model:value="minImportance" :min="1" :max="5" :step="1" />
          </div>

          <div>
            <label class="field-label">{{ copy.digest.sort }}</label>
            <n-radio-group v-model:value="sortBy" size="medium">
              <n-radio-button value="importance">{{ copy.digest.importance }}</n-radio-button>
              <n-radio-button value="published">{{ copy.digest.published }}</n-radio-button>
            </n-radio-group>
          </div>
        </div>
      </aside>

      <section class="results-column">
        <n-alert
          v-if="store.error"
          type="error"
          class="request-alert"
          :title="copy.digest.requestFailed"
        >
          {{ store.error }}
        </n-alert>

        <div class="paper-panel results-summary animate-fade-up delay-2">
          <div>
            <p class="eyebrow">{{ copy.digest.visibleResults }}</p>
            <h2 class="section-title">
              {{ visibleCount }} {{ copy.digest.items }}
            </h2>
          </div>

          <div class="chip-row">
            <span v-for="chip in activeFilterChips" :key="chip" class="soft-pill">
              {{ chip }}
            </span>
          </div>
        </div>

        <n-spin :show="store.loading && !store.currentDigest">
          <div v-if="store.currentDigest?.articles.length" class="article-stack">
            <ArticleCard
              v-for="(article, index) in store.currentDigest.articles"
              :key="article.id"
              :article="article"
              class="animate-fade-up"
              :style="{ animationDelay: `${Math.min(index * 40, 320) + 120}ms` }"
            />
          </div>

          <div v-else-if="!store.loading" class="paper-panel empty-panel">
            <n-empty :description="copy.digest.empty" />
          </div>
        </n-spin>
      </section>
    </div>
  </div>
</template>

<style scoped>
.digest-view {
  display: grid;
  gap: 28px;
}

.digest-hero,
.filter-rail,
.results-summary,
.empty-panel {
  padding: 30px;
}

.digest-hero {
  display: grid;
  gap: 22px;
}

.digest-hero__header {
  display: flex;
  justify-content: flex-start;
}

.back-button {
  padding-left: 0;
  color: var(--ink-soft);
}

.digest-hero__body {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.9fr);
  gap: 26px;
  align-items: end;
}

.digest-hero__copy {
  display: grid;
  gap: 14px;
}

.digest-metrics {
  align-self: stretch;
}

.digest-layout {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.filter-rail {
  position: sticky;
  top: 98px;
  display: grid;
  gap: 22px;
}

.filter-rail__header {
  display: grid;
  gap: 8px;
}

.results-column {
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

.article-stack {
  display: grid;
  gap: 18px;
}

.empty-panel {
  margin-top: 8px;
}

@media (max-width: 1024px) {
  .digest-hero__body,
  .digest-layout {
    grid-template-columns: 1fr;
  }

  .filter-rail {
    position: static;
  }
}

@media (max-width: 640px) {
  .digest-hero,
  .filter-rail,
  .results-summary,
  .empty-panel {
    padding: 22px;
  }
}
</style>
