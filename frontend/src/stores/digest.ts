import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { DailyDigest, DateList, QueryParams } from '../types';
import { getDates, getDigest } from '../api';

export const useDigestStore = defineStore('digest', () => {
  const dateList = ref<DateList>({ dates: [], latest: null });
  const currentDigest = ref<DailyDigest | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchDateList = async () => {
    loading.value = true;
    try {
      dateList.value = await getDates();
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch dates';
    } finally {
      loading.value = false;
    }
  };

  const fetchDigest = async (date: string, params: QueryParams = {}) => {
    loading.value = true;
    error.value = null;
    try {
      currentDigest.value = await getDigest(date, params);
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch digest';
    } finally {
      loading.value = false;
    }
  };

  return {
    dateList,
    currentDigest,
    loading,
    error,
    fetchDateList,
    fetchDigest,
  };
});
