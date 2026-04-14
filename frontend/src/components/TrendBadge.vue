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
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: var(--paper-surface);
  color: var(--ink-soft);
  font-size: 0.74rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.trend-badge--hot {
  color: #b5706a;
  background: rgba(181, 112, 106, 0.06);
  border-color: rgba(181, 112, 106, 0.12);
}

.trend-badge--rising {
  color: var(--accent);
  background: rgba(196, 149, 106, 0.06);
  border-color: rgba(196, 149, 106, 0.12);
}
</style>
