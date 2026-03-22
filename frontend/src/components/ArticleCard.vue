<script setup lang="ts">
import { computed } from 'vue';
import { NIcon } from 'naive-ui';
import { OpenOutline, TimeOutline } from '@vicons/ionicons5';
import dayjs from 'dayjs';
import { useLocale } from '../composables/useLocale';
import type { Article } from '../types';

const props = defineProps<{
  article: Article;
}>();

const { copy } = useLocale();

const categoryLabels = computed<Record<string, string>>(() => ({
  arxiv: copy.value.categories.arxiv,
  news: copy.value.categories.news,
  official: copy.value.categories.official,
  community: copy.value.categories.community,
}));

const importanceDots = computed(() =>
  Array.from({ length: 5 }, (_, index) => index < props.article.importance),
);

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm');
</script>

<template>
  <article class="article-card">
    <div class="article-card__header">
      <div class="article-card__eyebrow">
        <span class="article-card__category">
          {{ categoryLabels[article.source_category] ?? article.source_category }}
        </span>
        <span class="article-card__divider"></span>
        <span class="article-card__source">{{ article.source_name }}</span>
      </div>

      <div class="article-card__importance" :aria-label="`${copy.digest.importance}: ${article.importance}/5`">
        <span
          v-for="(filled, index) in importanceDots"
          :key="index"
          class="article-card__dot"
          :class="{ 'article-card__dot--filled': filled }"
        ></span>
        <span class="article-card__importance-label">{{ article.importance }}/5</span>
      </div>
    </div>

    <a :href="article.url" target="_blank" rel="noopener noreferrer" class="article-card__title">
      {{ article.title }}
    </a>

    <p class="article-card__summary">{{ article.summary_zh }}</p>

    <div class="article-card__footer">
      <div class="article-card__meta">
        <span class="soft-pill">
          <n-icon size="14">
            <TimeOutline />
          </n-icon>
          {{ formatDate(article.published) }}
        </span>

        <span v-for="tag in article.tags" :key="tag" class="soft-pill article-card__tag">
          #{{ tag }}
        </span>
      </div>

      <a :href="article.url" target="_blank" rel="noopener noreferrer" class="article-card__link">
        {{ copy.article.readSource }}
        <n-icon size="14">
          <OpenOutline />
        </n-icon>
      </a>
    </div>
  </article>
</template>

<style scoped>
.article-card {
  padding: 26px 28px;
  border-radius: 26px;
  border: 1px solid rgba(73, 58, 45, 0.1);
  background: linear-gradient(180deg, rgba(255, 253, 248, 0.92), rgba(250, 244, 235, 0.76));
  box-shadow: var(--shadow-card);
  display: grid;
  gap: 18px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.article-card:hover {
  transform: translateY(-1px);
  border-color: rgba(73, 58, 45, 0.16);
  box-shadow: var(--shadow-soft);
}

.article-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.article-card__eyebrow {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--ink-faint);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.article-card__category {
  color: var(--ink-soft);
  font-weight: 600;
}

.article-card__divider {
  width: 18px;
  height: 1px;
  background: rgba(73, 58, 45, 0.18);
}

.article-card__importance {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.article-card__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(127, 102, 83, 0.16);
}

.article-card__dot--filled {
  background: var(--accent);
}

.article-card__importance-label {
  margin-left: 4px;
  color: var(--ink-faint);
  font-size: 0.78rem;
}

.article-card__title {
  color: var(--ink-strong);
  text-decoration: none;
  font-family: var(--font-serif);
  font-size: clamp(1.55rem, 2vw, 2.2rem);
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.article-card__title:hover {
  color: var(--accent);
}

.article-card__summary {
  margin: 0;
  color: var(--ink);
  font-size: 1rem;
  line-height: 1.9;
}

.article-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 18px;
  border-top: 1px solid rgba(73, 58, 45, 0.08);
}

.article-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.article-card__tag {
  color: var(--ink-soft);
}

.article-card__link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-soft);
  text-decoration: none;
  white-space: nowrap;
}

.article-card__link:hover {
  color: var(--ink-strong);
}

@media (max-width: 680px) {
  .article-card {
    padding: 22px;
  }

  .article-card__header,
  .article-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
