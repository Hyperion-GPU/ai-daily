<script setup lang="ts">
import { NButton, NCard, NIcon, NRate, NSpace } from 'naive-ui';
import { OpenOutline, TimeOutline } from '@vicons/ionicons5';
import dayjs from 'dayjs';
import type { Article } from '../types';

defineProps<{
  article: Article;
}>();

const categoryColors: Record<string, string> = {
  arxiv: '#cc7b5d',
  news: '#6b8e6b',
  official: '#d4aa50',
  community: '#827397',
};

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm');
</script>

<template>
  <n-card class="article-card animate-fade-up" hoverable :bordered="false">
    <div class="card-content">
      <div class="card-header">
        <div class="category-overline" :style="{ color: categoryColors[article.source_category] }">
          {{ article.source_category.toUpperCase() }}
        </div>
        <div class="title-row">
          <a :href="article.url" target="_blank" class="title-link">
            {{ article.title }}
          </a>
          <n-rate readonly :default-value="article.importance" size="small" :color="'#d4aa50'" class="rate-stars" />
        </div>
        <div class="meta-row">
          <span class="source-name">{{ article.source_name }}</span>
          <span class="meta-divider">&middot;</span>
          <span class="publish-time">
            <n-icon><TimeOutline /></n-icon>
            {{ formatDate(article.published) }}
          </span>
        </div>
      </div>

      <p class="summary">{{ article.summary_zh }}</p>

      <div class="card-footer">
        <n-space size="small" class="tags-space">
          <span v-for="tag in article.tags" :key="tag" class="text-tag">#{{ tag }}</span>
        </n-space>

        <n-button text tag="a" :href="article.url" target="_blank" class="read-more">
          Read source
          <template #icon>
            <n-icon><OpenOutline /></n-icon>
          </template>
        </n-button>
      </div>
    </div>
  </n-card>
</template>

<style scoped>
.article-card {
  margin-bottom: 24px;
  background-color: var(--n-card-color);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03), 0 1px 4px rgba(0, 0, 0, 0.02);
  transition:
    transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
  border: 1px solid var(--n-border-color);
}

.is-dark .article-card {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 1px 4px rgba(0, 0, 0, 0.1);
}

:deep(.n-card__content) {
  padding: 32px !important;
}

.article-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.06), 0 4px 12px rgba(0, 0, 0, 0.03);
  border-color: var(--n-primary-color);
}

.is-dark .article-card:hover {
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.4), 0 4px 12px rgba(0, 0, 0, 0.2);
}

.card-header {
  margin-bottom: 16px;
}

.category-overline {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.title-link {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 500;
  color: var(--n-text-color);
  text-decoration: none;
  line-height: 1.35;
  transition: color 0.2s;
  letter-spacing: -0.01em;
}

.title-link:hover {
  color: var(--n-primary-color);
}

.rate-stars {
  flex-shrink: 0;
  margin-top: 6px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--n-text-color-3);
}

.source-name {
  color: var(--n-text-color-2);
  font-weight: 500;
}

.meta-divider {
  color: var(--n-border-color);
  font-weight: bold;
}

.publish-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.summary {
  font-size: 16px;
  color: var(--n-text-color-2);
  line-height: 1.7;
  margin: 20px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--n-border-color);
  gap: 16px;
}

.tags-space {
  margin-right: auto;
}

.text-tag {
  font-size: 13px;
  color: var(--n-text-color-3);
  background-color: transparent;
  padding: 2px 0;
  transition: color 0.2s;
}

.text-tag:hover {
  color: var(--n-text-color-2);
}

.read-more {
  color: var(--n-text-color-3);
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.read-more:hover {
  color: var(--n-primary-color);
}

@media (max-width: 640px) {
  :deep(.n-card__content) {
    padding: 20px !important;
  }

  .title-link {
    font-size: 20px;
  }

  .title-row {
    flex-direction: column;
  }

  .card-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>
