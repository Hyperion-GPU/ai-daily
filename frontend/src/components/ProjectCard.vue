<script setup lang="ts">
import { computed } from 'vue';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';
import { useLocale } from '../composables/useLocale';
import type { GitHubProject } from '../types';
import LanguageDot from './LanguageDot.vue';
import StatsBar from './StatsBar.vue';
import TrendBadge from './TrendBadge.vue';

dayjs.extend(relativeTime);

const props = defineProps<{
  project: GitHubProject;
}>();

const { copy, locale } = useLocale();

const trend = computed(() => props.project.trend ?? null);
const starsToday = computed(() => props.project.stars_today ?? null);
const starsWeekly = computed(() => props.project.stars_weekly ?? null);

const timeAgo = computed(() => {
  if (!props.project.pushed_at) {
    return null;
  }

  const date = dayjs(props.project.pushed_at);
  if (locale.value === 'zh') {
    return copy.value.github.updatedAgo.replace('{time}', date.locale('zh-cn').fromNow(true));
  }
  return copy.value.github.updatedAgo.replace('{time}', date.locale('en').fromNow(true));
});
</script>

<template>
  <article class="project-card">
    <div class="project-card__header">
      <div class="project-card__heading">
        <div class="project-card__meta-row">
          <span class="soft-pill">{{ project.category }}</span>
          <TrendBadge :trend="trend" />
        </div>
        <a :href="project.html_url" target="_blank" rel="noopener noreferrer" class="project-card__title">
          {{ project.full_name }}
        </a>
      </div>
      <a :href="project.html_url" target="_blank" rel="noopener noreferrer" class="project-card__action">
        {{ copy.github.viewProject }}
      </a>
    </div>

    <p v-if="project.description" class="project-card__description project-card__description--en">
      {{ project.description }}
    </p>
    <p v-if="project.description_zh" class="project-card__description">
      {{ project.description_zh }}
    </p>

    <StatsBar
      :stars="project.stars"
      :forks="project.forks"
      :issues="project.open_issues"
      :stars-today="starsToday"
      :stars-weekly="starsWeekly"
    />

    <div class="project-card__footer">
      <div class="project-card__meta">
        <LanguageDot v-if="project.language" :language="project.language" />
        <span v-if="project.license" class="soft-pill">{{ project.license }}</span>
        <span v-if="timeAgo" class="soft-pill">{{ timeAgo }}</span>
      </div>

      <div class="project-card__topics">
        <span v-for="topic in project.topics?.slice(0, 5)" :key="topic" class="soft-pill project-card__topic">
          #{{ topic }}
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.project-card {
  padding: 24px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line);
  background: var(--paper-elevated);
  display: grid;
  gap: 16px;
  transition: border-color 0.15s ease;
}

.project-card:hover {
  border-color: rgba(0, 0, 0, 0.14);
}

.project-card__header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 18px;
}

.project-card__heading {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.project-card__meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.project-card__title {
  color: var(--ink-strong);
  text-decoration: none;
  font-family: var(--font-heading);
  font-size: clamp(1.3rem, 1.8vw, 1.75rem);
  font-weight: 500;
  line-height: 1.18;
  letter-spacing: -0.025em;
}

.project-card__title:hover {
  color: var(--ink-strong);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}

.project-card__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: var(--paper-surface);
  color: var(--ink-soft);
  text-decoration: none;
  white-space: nowrap;
}

.project-card__action:hover {
  color: var(--ink-strong);
}

.project-card__description {
  margin: 0;
  color: var(--ink);
  font-size: 1rem;
  line-height: 1.82;
}

.project-card__description--en {
  color: var(--ink-soft);
}

.project-card__footer {
  display: grid;
  gap: 14px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.project-card__meta,
.project-card__topics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.project-card__topic {
  color: var(--ink-soft);
}

@media (max-width: 680px) {
  .project-card {
    padding: 20px;
  }

  .project-card__header {
    flex-direction: column;
  }
}
</style>
