<script setup lang="ts">
import { computed } from 'vue';
import { useLocale } from '../composables/useLocale';

const props = defineProps<{
  stars: number;
  forks: number;
  issues: number;
  starsToday: number | null;
  starsWeekly: number | null;
}>();

const { copy } = useLocale();

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}m`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  }
  return `${num}`;
};

const items = computed(() => [
  { key: 'stars', label: copy.value.github.stars, value: formatNumber(props.stars) },
  { key: 'forks', label: copy.value.github.forks, value: formatNumber(props.forks) },
  { key: 'issues', label: copy.value.github.issues, value: formatNumber(props.issues) },
  ...(props.starsToday && props.starsToday > 0
    ? [{ key: 'stars-today', label: copy.value.github.starsToday, value: formatNumber(props.starsToday) }]
    : []),
  ...(props.starsWeekly && props.starsWeekly > 0
    ? [{ key: 'stars-weekly', label: copy.value.github.starsWeekly, value: formatNumber(props.starsWeekly) }]
    : []),
]);
</script>

<template>
  <div class="stats-bar">
    <div v-for="item in items" :key="item.key" class="stats-bar__item">
      <span class="stats-bar__value">{{ item.value }}</span>
      <span class="stats-bar__label">{{ item.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.stats-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  gap: 10px;
}

.stats-bar__item {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(73, 58, 45, 0.08);
  background: rgba(255, 252, 247, 0.72);
}

.stats-bar__value {
  display: block;
  margin-bottom: 6px;
  color: var(--ink-strong);
  font-family: var(--font-serif);
  font-size: 1.35rem;
  line-height: 1;
}

.stats-bar__label {
  color: var(--ink-faint);
  font-size: 0.76rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
</style>
