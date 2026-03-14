<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { NEmpty, NIcon, NList, NListItem, NSpin, NTag } from 'naive-ui';
import { CalendarOutline, ChevronForward, DocumentTextOutline } from '@vicons/ionicons5';
import { useDigestStore } from '../stores/digest';
import type { DateEntry } from '../types';

const store = useDigestStore();
const router = useRouter();

const pageTitle = 'Digest Archive';
const pageDescription = 'Browse generated AI Daily digests by date.';
const latestLabel = 'Latest';
const articlesLabel = 'articles';
const emptyLabel = 'No digest is available yet.';

const categoryLabels: Record<string, string> = {
  arxiv: 'Arxiv',
  official: 'Official',
  news: 'News',
  community: 'Community',
};

const categoryTagType = (
  category: string,
): 'default' | 'success' | 'warning' | 'info' => {
  switch (category) {
    case 'official':
      return 'success';
    case 'news':
      return 'warning';
    case 'community':
      return 'info';
    default:
      return 'default';
  }
};

const categoryEntries = (entry: DateEntry) =>
  Object.entries(entry.by_category ?? {}).sort((a, b) => b[1] - a[1]);

onMounted(() => {
  void store.fetchDateList();
});

const goToDigest = (date: string) => {
  router.push({ name: 'digest', params: { date } });
};
</script>

<template>
  <div class="home-view">
    <div class="view-header animate-fade-up">
      <h2>{{ pageTitle }}</h2>
      <p>{{ pageDescription }}</p>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.dateList.dates.length > 0" class="date-list animate-fade-up delay-1">
        <n-list hoverable clickable bordered>
          <n-list-item
            v-for="(entry, index) in store.dateList.dates"
            :key="entry.date"
            @click="goToDigest(entry.date)"
            class="animate-fade-up"
            :style="{ animationDelay: `${index * 40 + 100}ms` }"
          >
            <template #prefix>
              <n-icon size="24" class="icon-muted">
                <CalendarOutline />
              </n-icon>
            </template>
            <div class="date-item-main">
              <div class="date-item-head">
                <div class="date-title-group">
                  <span class="date-title">{{ entry.date }}</span>
                  <span v-if="entry.date === store.dateList.latest" class="latest-badge">{{ latestLabel }}</span>
                </div>
                <div class="article-total">
                  <n-icon size="16">
                    <DocumentTextOutline />
                  </n-icon>
                  <span>{{ entry.total }} {{ articlesLabel }}</span>
                </div>
              </div>
              <div class="category-tags">
                <n-tag
                  v-for="[category, count] in categoryEntries(entry)"
                  :key="category"
                  :type="categoryTagType(category)"
                  size="small"
                  round
                  :bordered="false"
                >
                  {{ categoryLabels[category] ?? category }} {{ count }}
                </n-tag>
              </div>
            </div>
            <template #suffix>
              <n-icon size="20" class="icon-muted">
                <ChevronForward />
              </n-icon>
            </template>
          </n-list-item>
        </n-list>
      </div>

      <n-empty v-else-if="!store.loading" :description="emptyLabel" class="animate-fade-up delay-2" />
    </n-spin>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 860px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 40px;
  text-align: center;
}

h2 {
  font-family: var(--font-serif);
  font-size: 36px;
  font-weight: 500;
  margin-bottom: 12px;
  color: var(--n-text-color);
  letter-spacing: -0.02em;
}

p {
  color: var(--n-text-color-3);
  font-size: 16px;
}

.date-list {
  background-color: var(--n-card-color);
  border-radius: 16px;
  border: 1px solid var(--n-border-color);
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03), 0 2px 8px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
  margin-top: 16px;
}

.is-dark .date-list {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.n-list) {
  --n-border-color: transparent !important;
  background-color: transparent;
}

:deep(.n-list-item) {
  padding: 20px 24px !important;
  border-bottom: 1px solid var(--n-border-color) !important;
}

:deep(.n-list-item:last-child) {
  border-bottom: none !important;
}

.date-item-main {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 10px;
}

.date-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.date-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.date-title {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 500;
  color: var(--n-text-color);
}

.latest-badge {
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--n-primary-color);
  opacity: 0.85;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.article-total {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--n-text-color-2);
  white-space: nowrap;
}

.icon-muted {
  color: var(--n-text-color-3);
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 640px) {
  .date-item-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
