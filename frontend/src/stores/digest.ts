import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { DailyDigest, DateList, QueryParams } from '../types';
import { getDates, getDigest } from '../api';

export const useDigestStore = defineStore('digest', () => {
  const dateList = ref<DateList>({ dates: [], latest: null });
  const currentDigest = ref<DailyDigest | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const digestRequestId = ref(0);
  const allTags = ref<string[]>([]);
  const allTagsDate = ref<string | null>(null);

  const getErrorMessage = (err: unknown, fallback: string) => {
    if (err instanceof Error && err.message) {
      return err.message;
    }
    return fallback;
  };

  const isUnfilteredDigestQuery = (params: QueryParams) =>
    !params.q &&
    !params.category &&
    (!params.tags || params.tags.length === 0) &&
    (params.min_importance ?? 1) === 1;

  const clearTagCache = () => {
    allTags.value = [];
    allTagsDate.value = null;
  };

  const fetchDateList = async () => {
    loading.value = true;
    error.value = null;
    try {
      dateList.value = await getDates();
    } catch (err: unknown) {
      error.value = getErrorMessage(err, 'Failed to fetch dates');
    } finally {
      loading.value = false;
    }
  };

  const fetchDigest = async (date: string, params: QueryParams = {}) => {
    const requestId = ++digestRequestId.value;
    loading.value = true;
    error.value = null;
    try {
      const digest = await getDigest(date, params);
      if (requestId !== digestRequestId.value) {
        return;
      }
      currentDigest.value = digest;
      if (isUnfilteredDigestQuery(params)) {
        allTags.value = Object.keys(digest.stats.by_tag ?? {});
        allTagsDate.value = date;
      }
    } catch (err: unknown) {
      if (requestId !== digestRequestId.value) {
        return;
      }
      currentDigest.value = null;
      error.value = getErrorMessage(err, 'Failed to fetch digest');
    } finally {
      if (requestId === digestRequestId.value) {
        loading.value = false;
      }
    }
  };

  return {
    dateList,
    currentDigest,
    loading,
    error,
    allTags,
    allTagsDate,
    clearTagCache,
    fetchDateList,
    fetchDigest,
  };
});
