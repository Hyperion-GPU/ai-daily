<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useDigestStore } from '../stores/digest';
import { NList, NListItem, NThing, NEmpty, NSpin, NIcon } from 'naive-ui';
import { CalendarOutline, ChevronForward } from '@vicons/ionicons5';

const store = useDigestStore();
const router = useRouter();

onMounted(() => {
  store.fetchDateList();
});

const goToDigest = (date: string) => {
  router.push({ name: 'digest', params: { date } });
};
</script>

<template>
  <div class="home-view">
    <div class="view-header">
      <h2>历史日报</h2>
      <p>选择日期查看 AI 资讯摘要</p>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.dateList.dates.length > 0" class="date-list">
        <n-list hoverable clickable bordered>
          <n-list-item
            v-for="date in store.dateList.dates"
            :key="date"
            @click="goToDigest(date)"
          >
            <template #prefix>
              <n-icon size="24" color="#8b949e">
                <CalendarOutline />
              </n-icon>
            </template>
            <n-thing :title="date" :description="date === store.dateList.latest ? '最新更新' : ''">
            </n-thing>
            <template #suffix>
              <n-icon size="20" color="#30363d">
                <ChevronForward />
              </n-icon>
            </template>
          </n-list-item>
        </n-list>
      </div>

      <n-empty v-else-if="!store.loading" description="暂无日报数据" />
    </n-spin>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 800px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 32px;
  text-align: center;
}

h2 {
  font-size: 28px;
  margin-bottom: 8px;
  color: #f0f6fc;
}

p {
  color: #8b949e;
  font-size: 16px;
}

.date-list {
  background-color: #161b22;
  border-radius: 8px;
  overflow: hidden;
}

:deep(.n-list) {
  --n-border-color: #30363d !important;
}

:deep(.n-list-item) {
  padding: 16px 24px !important;
  transition: background-color 0.2s;
}

:deep(.n-list-item:hover) {
  background-color: #1c2128 !important;
}

:deep(.n-thing-main__title) {
  font-size: 18px !important;
  font-weight: 500 !important;
}
</style>
