<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NEmpty, NIcon, NSpin, useMessage } from 'naive-ui';
import { CalendarOutline, ChevronForward, RefreshOutline } from '@vicons/ionicons5';
import { useLocale } from '../composables/useLocale';
import { PIPELINE_ALREADY_RUNNING, useDigestStore } from '../stores/digest';
import type { DateEntry, PipelineStatus } from '../types';

const store = useDigestStore();
const router = useRouter();
const message = useMessage();
const { copy, dateTimeLocale } = useLocale();

const latestEntry = computed(() => store.dateList.dates[0] ?? null);
const archiveArticleCount = computed(() =>
  store.dateList.dates.reduce((sum, entry) => sum + entry.total, 0),
);

const pipelineButtonLabel = computed(() =>
  store.pipelineStatus.running ? copy.value.home.fetchRunning : copy.value.home.fetchToday,
);

const progressStageLabel = computed(() => {
  const stage = store.pipelineStatus.progress?.stage;
  switch (stage) {
    case 'starting':
      return copy.value.home.progressStarting;
    case 'fetching':
      return copy.value.home.progressFetching;
    case 'stage1':
      return copy.value.home.progressStage1;
    case 'stage2':
      return copy.value.home.progressStage2;
    case 'finalizing':
      return copy.value.home.progressFinalizing;
    case 'completed':
      return copy.value.home.progressCompleted;
    case 'error':
      return copy.value.home.progressError;
    default:
      return copy.value.home.progressIdle;
  }
});

const progressPercent = computed(() => {
  const stage = store.pipelineStatus.progress?.stage;
  const current = store.pipelineStatus.progress?.current;
  const total = store.pipelineStatus.progress?.total;
  if (typeof current !== 'number' || typeof total !== 'number' || total <= 0) {
    switch (stage) {
      case 'starting':
        return 5;
      case 'fetching':
        return 18;
      case 'stage1':
        return 42;
      case 'stage2':
        return 74;
      case 'finalizing':
        return 92;
      case 'completed':
      case 'error':
        return 100;
      default:
        return 0;
    }
  }
  return Math.max(0, Math.min(100, Math.round((current / total) * 100)));
});

const progressStats = computed(() => {
  const progress = store.pipelineStatus.progress;
  if (!progress) {
    return [];
  }

  return [
    {
      key: 'candidates',
      label: copy.value.home.progressCandidates,
      value: progress.candidates,
    },
    {
      key: 'selected',
      label: copy.value.home.progressSelected,
      value: progress.selected,
    },
    {
      key: 'processed',
      label: copy.value.home.progressProcessed,
      value: progress.processed,
    },
    {
      key: 'report',
      label: copy.value.home.progressReport,
      value: progress.report_articles,
    },
  ].filter((item) => typeof item.value === 'number');
});

const statusNote = computed(() => {
  if (store.pipelineStatus.running && store.pipelineStatus.progress?.message) {
    return store.pipelineStatus.progress.message;
  }

  if (store.pipelineStatus.last_run) {
    return new Intl.DateTimeFormat(dateTimeLocale.value, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(store.pipelineStatus.last_run));
  }

  return copy.value.home.progressIdle;
});

const formatDate = (date: string) => {
  const value = new Date(`${date}T00:00:00`);
  if (Number.isNaN(value.getTime())) {
    return date;
  }
  return new Intl.DateTimeFormat(dateTimeLocale.value, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(value);
};

const categoryEntries = (entry: DateEntry) =>
  Object.entries(entry.by_category ?? {}).sort((a, b) => b[1] - a[1]);

const categoryLabelMap = computed<Record<string, string>>(() => ({
  arxiv: copy.value.categories.arxiv,
  official: copy.value.categories.official,
  news: copy.value.categories.news,
  community: copy.value.categories.community,
}));

const handlePipelineSettled = (status: PipelineStatus) => {
  if (status.error || status.last_outcome === 'error') {
    message.error(status.error || copy.value.home.fetchError);
    return;
  }

  if (status.last_outcome === 'no_new_items') {
    message.info(copy.value.home.fetchNoUpdates);
    return;
  }

  message.success(copy.value.home.fetchSuccess);
};

const initializeView = async () => {
  await store.fetchDateList();
  const status = await store.refreshPipelineStatus();
  if (status.running) {
    store.startPipelinePolling(handlePipelineSettled);
  }
};

onMounted(() => {
  void initializeView();
});

onBeforeUnmount(() => {
  store.stopPipelinePolling();
});

const fetchToday = async () => {
  if (store.pipelineStatus.running) {
    message.warning(copy.value.home.fetchAlreadyRunning);
    return;
  }

  try {
    await store.triggerPipeline();
    store.startPipelinePolling(handlePipelineSettled);
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : copy.value.home.fetchError;
    if (errorMessage === PIPELINE_ALREADY_RUNNING) {
      message.warning(copy.value.home.fetchAlreadyRunning);
      store.startPipelinePolling(handlePipelineSettled);
      return;
    }
    message.error(errorMessage || copy.value.home.fetchError);
  }
};

const goToDigest = (date: string) => {
  void router.push({ name: 'digest', params: { date } });
};
</script>

<template>
  <div class="home-view">
    <section class="hero-grid">
      <div class="paper-panel hero-copy animate-fade-up">
        <p class="eyebrow">AI Daily</p>
        <h1 class="editorial-title">{{ copy.home.pageTitle }}</h1>
        <p class="lede">
          {{ copy.home.pageDescription }}
        </p>

        <div class="metric-grid hero-metrics">
          <div class="metric-card">
            <span class="metric-value">{{ store.dateList.dates.length }}</span>
            <span class="metric-label">Archive</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{{ archiveArticleCount }}</span>
            <span class="metric-label">{{ copy.home.articles }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{{ latestEntry ? formatDate(latestEntry.date) : '—' }}</span>
            <span class="metric-label">{{ copy.home.latest }}</span>
          </div>
        </div>

        <div class="hero-actions">
          <n-button
            type="primary"
            size="large"
            class="primary-action"
            :loading="store.pipelineStatus.running"
            @click="fetchToday"
          >
            <template #icon>
              <n-icon>
                <RefreshOutline />
              </n-icon>
            </template>
            {{ pipelineButtonLabel }}
          </n-button>

          <router-link
            v-if="store.dateList.latest"
            :to="{ name: 'digest', params: { date: store.dateList.latest } }"
            class="secondary-link"
          >
            <span>{{ copy.home.latest }}</span>
            <n-icon>
              <ChevronForward />
            </n-icon>
          </router-link>
        </div>
      </div>

      <aside class="paper-panel status-panel animate-fade-up delay-1">
        <div class="status-panel__top">
          <p class="eyebrow">{{ copy.home.progressTitle }}</p>
          <span class="soft-pill" :class="{ 'soft-pill--live': store.pipelineStatus.running }">
            <span class="status-dot" :class="{ 'status-dot--live': store.pipelineStatus.running }"></span>
            {{ progressStageLabel }}
          </span>
        </div>

        <p class="status-note">
          {{ statusNote }}
        </p>

        <div class="progress-track" aria-hidden="true">
          <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
        </div>

        <div v-if="progressStats.length > 0" class="status-metrics">
          <div v-for="item in progressStats" :key="item.key" class="status-metric">
            <span class="status-metric__label">{{ item.label }}</span>
            <span class="status-metric__value">{{ item.value }}</span>
          </div>
        </div>

        <div v-else class="status-placeholder">
          <div class="status-placeholder__label">{{ copy.home.progressTitle }}</div>
          <div class="status-placeholder__value">{{ copy.home.progressIdle }}</div>
        </div>
      </aside>
    </section>

    <section class="paper-panel archive-panel animate-fade-up delay-2">
      <div class="archive-panel__header">
        <div>
          <p class="eyebrow">{{ copy.home.pageTitle }}</p>
          <h2 class="section-title">{{ copy.home.latest }}</h2>
        </div>
        <div class="soft-pill archive-note">
          <n-icon size="16">
            <CalendarOutline />
          </n-icon>
          <span>{{ store.dateList.latest ? formatDate(store.dateList.latest) : copy.home.empty }}</span>
        </div>
      </div>

      <n-spin :show="store.loading">
        <div v-if="store.dateList.dates.length > 0" class="archive-list">
          <button
            v-for="(entry, index) in store.dateList.dates"
            :key="entry.date"
            type="button"
            class="archive-row animate-fade-up"
            :style="{ animationDelay: `${Math.min(index * 50, 360) + 140}ms` }"
            @click="goToDigest(entry.date)"
          >
            <div class="archive-row__meta">
              <div class="archive-row__heading">
                <span class="archive-row__date">{{ formatDate(entry.date) }}</span>
                <span v-if="entry.date === store.dateList.latest" class="archive-row__badge">
                  {{ copy.home.latest }}
                </span>
              </div>
              <div class="chip-row">
                <span
                  v-for="[category, count] in categoryEntries(entry)"
                  :key="category"
                  class="soft-pill archive-chip"
                >
                  <span>{{ categoryLabelMap[category] ?? category }}</span>
                  <strong>{{ count }}</strong>
                </span>
              </div>
            </div>

            <div class="archive-row__side">
              <span class="archive-row__count">{{ entry.total }}</span>
              <span class="archive-row__label">{{ copy.home.articles }}</span>
              <n-icon class="archive-row__icon">
                <ChevronForward />
              </n-icon>
            </div>
          </button>
        </div>

        <div v-else class="empty-panel">
          <n-empty :description="copy.home.empty" />
        </div>
      </n-spin>
    </section>
  </div>
</template>

<style scoped>
.home-view {
  display: grid;
  gap: 28px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(300px, 0.85fr);
  gap: 24px;
}

.hero-copy,
.status-panel,
.archive-panel {
  padding: 28px;
}

.hero-copy {
  display: grid;
  gap: 24px;
}

.hero-metrics {
  margin-top: 4px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
}

.primary-action {
  min-width: 198px;
}

.secondary-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 13px 18px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: var(--paper-surface);
  text-decoration: none;
  color: var(--ink);
}

.status-panel {
  display: grid;
  align-content: start;
  gap: 16px;
}

.status-panel__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.soft-pill--live {
  color: var(--ink-strong);
  border-color: rgba(217, 119, 87, 0.2);
  background: rgba(217, 119, 87, 0.06);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.12);
}

.status-dot--live {
  background: var(--accent);
  box-shadow: 0 0 0 4px rgba(217, 119, 87, 0.1);
}

.status-note {
  margin: 0;
  font-size: 1rem;
  line-height: 1.75;
  color: var(--ink);
}

.progress-track {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 0.35s ease;
}

.status-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.status-metric,
.status-placeholder {
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background: var(--paper-surface);
}

.status-metric__label,
.status-placeholder__label {
  display: block;
  margin-bottom: 8px;
  color: var(--ink-faint);
  font-size: 0.76rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.status-metric__value,
.status-placeholder__value {
  color: var(--ink-strong);
  font-family: var(--font-serif);
  font-size: 1.4rem;
  line-height: 1;
}

.archive-panel {
  display: grid;
  gap: 24px;
}

.archive-panel__header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.archive-note {
  white-space: nowrap;
}

.archive-list {
  display: grid;
  gap: 12px;
}

.archive-row {
  width: 100%;
  padding: 18px 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--paper-surface);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.archive-row:hover {
  border-color: rgba(0, 0, 0, 0.14);
  box-shadow: var(--shadow-soft);
}

.archive-row__meta {
  min-width: 0;
  display: grid;
  gap: 14px;
}

.archive-row__heading {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.archive-row__date {
  color: var(--ink-strong);
  font-family: var(--font-serif);
  font-size: 1.45rem;
  line-height: 1.1;
}

.archive-row__badge {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: var(--ink-soft);
  font-size: 0.76rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.archive-chip strong {
  color: var(--ink-strong);
  font-weight: 600;
}

.archive-row__side {
  display: grid;
  align-content: center;
  justify-items: end;
  gap: 4px;
  min-width: 78px;
}

.archive-row__count {
  color: var(--ink-strong);
  font-family: var(--font-serif);
  font-size: 2rem;
  line-height: 1;
}

.archive-row__label {
  color: var(--ink-faint);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.archive-row__icon {
  color: var(--ink-faint);
}

.empty-panel {
  padding: 30px 0 10px;
}

@media (max-width: 980px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .hero-copy,
  .status-panel,
  .archive-panel {
    padding: 20px;
  }

  .archive-panel__header,
  .archive-row {
    grid-template-columns: 1fr;
  }

  .archive-row__side {
    justify-items: start;
  }

  .status-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
