<script setup lang="ts">
import { computed } from 'vue';
import { useLocale } from '../composables/useLocale';

const props = defineProps<{
  trend: 'hot' | 'rising' | 'stable' | null;
}>();

const { copy } = useLocale();

const label = computed(() => {
  if (props.trend === 'hot') return copy.value.github.trendHot;
  if (props.trend === 'rising') return copy.value.github.trendRising;
  if (props.trend === 'stable') return copy.value.github.trendStable;
  return '';
});
</script>

<template>
  <span v-if="trend" class="trend-badge" :class="`trend-badge--${trend}`">
    {{ label }}
  </span>
</template>

<style scoped>
.trend-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 11px;
  border-radius: 999px;
  border: 1px solid rgba(73, 58, 45, 0.1);
  background: rgba(255, 252, 246, 0.82);
  color: var(--ink-soft);
  font-size: 0.74rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.trend-badge--hot {
  color: #7d5148;
  background: rgba(155, 91, 82, 0.08);
}

.trend-badge--rising {
  color: #7f6653;
  background: rgba(127, 102, 83, 0.08);
}
</style>
