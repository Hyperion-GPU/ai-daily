<script setup lang="ts">
import { computed } from 'vue';
import { useLocale } from '../composables/useLocale';
import type { GitHubFetchProgress } from '../types';

const props = defineProps<{
  running: boolean;
  progress: GitHubFetchProgress | null;
  error?: string | null;
}>();

const { copy } = useLocale();

const percent = computed(() => {
  if (props.progress?.stage === 'completed') return 100;
  if (!props.progress?.topics_total || !props.progress?.topics_done) {
    if (props.progress?.stage === 'starting') return 6;
    if (props.progress?.stage === 'searching') return 28;
    if (props.progress?.stage === 'deduplicating') return 74;
    if (props.progress?.stage === 'computing_trends') return 88;
    if (props.progress?.stage === 'saving') return 96;
    return 0;
  }

  return Math.min(82, Math.round((props.progress.topics_done / props.progress.topics_total) * 82));
});

const stageDescription = computed(() => {
  if (props.error) return props.error;
  switch (props.progress?.stage) {
    case 'starting':
      return copy.value.github.progressStarting;
    case 'searching':
      return props.progress.message || copy.value.github.progressSearching;
    case 'deduplicating':
      return copy.value.github.progressDedup;
    case 'computing_trends':
      return copy.value.github.progressTrends;
    case 'saving':
      return copy.value.github.progressSaving;
    case 'completed':
      return copy.value.github.progressCompleted;
    case 'error':
      return copy.value.github.progressError;
    default:
      return '';
  }
});

const progressItems = computed(() =>
  [
    {
      key: 'topics',
      label: copy.value.github.progressTopics,
      value:
        props.progress?.topics_done != null && props.progress?.topics_total != null
          ? `${props.progress.topics_done} / ${props.progress.topics_total}`
          : '—',
    },
    {
      key: 'found',
      label: copy.value.github.progressFound,
      value: props.progress?.projects_found ?? '—',
    },
    {
      key: 'new',
      label: copy.value.github.progressNew,
      value: props.progress?.projects_new ?? '—',
    },
  ],
);
</script>

<template>
  <section v-if="running || error" class="paper-panel progress-card">
    <div class="progress-card__header">
      <div>
        <p class="eyebrow">{{ copy.github.progressTitle }}</p>
        <h2 class="section-title">{{ stageDescription || copy.github.fetchRunning }}</h2>
      </div>
      <span class="soft-pill" :class="{ 'progress-card__pill--error': !!error }">
        {{ percent }}%
      </span>
    </div>

    <div class="progress-card__track" aria-hidden="true">
      <div class="progress-card__fill" :class="{ 'progress-card__fill--error': !!error }" :style="{ width: `${percent}%` }"></div>
    </div>

    <div class="progress-card__metrics">
      <div v-for="item in progressItems" :key="item.key" class="progress-card__metric">
        <span class="progress-card__metric-label">{{ item.label }}</span>
        <span class="progress-card__metric-value">{{ item.value }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.progress-card {
  padding: 24px;
  display: grid;
  gap: 16px;
}

.progress-card__header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}

.progress-card__pill--error {
  color: var(--danger);
  background: rgba(194, 86, 80, 0.06);
}

.progress-card__track {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.progress-card__fill {
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 0.35s ease;
}

.progress-card__fill--error {
  background: var(--danger);
}

.progress-card__metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.progress-card__metric {
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background: var(--paper-surface);
}

.progress-card__metric-label {
  display: block;
  margin-bottom: 8px;
  color: var(--ink-faint);
  font-size: 0.76rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.progress-card__metric-value {
  color: var(--ink-strong);
  font-family: var(--font-serif);
  font-size: 1.4rem;
  line-height: 1;
}

@media (max-width: 640px) {
  .progress-card {
    padding: 20px;
  }

  .progress-card__header {
    flex-direction: column;
  }
}
</style>
