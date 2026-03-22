<script setup lang="ts">
const props = defineProps<{
  language: string;
}>();
</script>

<template>
  <span class="language-pill">
    <span class="language-pill__dot"></span>
    <span>{{ props.language }}</span>
  </span>
</template>

<style scoped>
.language-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-soft);
}

.language-pill__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(127, 102, 83, 0.45);
}
</style>
