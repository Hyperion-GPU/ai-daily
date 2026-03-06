<script setup lang="ts">
import { NCard, NTag, NSpace, NRate, NButton, NIcon } from 'naive-ui';
import { OpenOutline, TimeOutline } from '@vicons/ionicons5';
import type { Article } from '../types';
import dayjs from 'dayjs';

defineProps<{
  article: Article;
}>();

const categoryColors: Record<string, string> = {
  arxiv: '#58a6ff',
  news: '#238636',
  official: '#f1e05a',
  community: '#a371f7',
};

const formatDate = (date: string) => dayjs(date).format('HH:mm');
</script>

<template>
  <n-card class="article-card" hoverable>
    <div class="card-content">
      <div class="card-header">
        <div class="title-row">
          <a :href="article.url" target="_blank" class="title-link">
            {{ article.title }}
          </a>
          <n-rate readonly :default-value="article.importance" size="small" :color="'#f1e05a'" />
        </div>
        <div class="meta-row">
          <n-tag
            :color="{ textColor: categoryColors[article.source_category], borderColor: categoryColors[article.source_category] }"
            size="small"
            round
            ghost
          >
            {{ article.source_category.toUpperCase() }}
          </n-tag>
          <span class="source-name">{{ article.source_name }}</span>
          <span class="publish-time">
            <n-icon><TimeOutline /></n-icon>
            {{ formatDate(article.published) }}
          </span>
        </div>
      </div>

      <p class="summary">{{ article.summary_zh }}</p>

      <div class="card-footer">
        <n-space size="small">
          <n-tag v-for="tag in article.tags" :key="tag" size="small" :bordered="false" class="tag"> # {{ tag }} </n-tag>
        </n-space>

        <n-button text tag="a" :href="article.url" target="_blank" class="read-more">
          查看原文
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
  margin-bottom: 16px;
  background-color: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  transition: transform 0.1s ease, border-color 0.1s ease;
}

.article-card:hover {
  border-color: #8b949e;
}

.card-header {
  margin-bottom: 12px;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.title-link {
  font-size: 18px;
  font-weight: 600;
  color: #58a6ff;
  text-decoration: none;
  line-height: 1.4;
}

.title-link:hover {
  text-decoration: underline;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #8b949e;
}

.source-name {
  color: #c9d1d9;
}

.publish-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.summary {
  font-size: 15px;
  color: #c9d1d9;
  line-height: 1.6;
  margin: 12px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  gap: 16px;
}

.tag {
  background-color: #21262d;
  color: #8b949e;
  font-size: 12px;
}

.read-more {
  color: #8b949e;
  font-size: 14px;
}

.read-more:hover {
  color: #58a6ff;
}

@media (max-width: 640px) {
  .title-row {
    flex-direction: column;
  }

  .card-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
