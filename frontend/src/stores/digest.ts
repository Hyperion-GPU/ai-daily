import { AxiosError } from 'axios';
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { DailyDigest, DateList, PipelineProgress, PipelineRunResponse, PipelineStatus, QueryParams } from '../types';
import { getDates, getDigest, getPipelineStatus, triggerPipeline as triggerPipelineRequest } from '../api';

const DEFAULT_PIPELINE_PROGRESS: PipelineProgress = {
  stage: null,
  message: null,
  current: null,
  total: null,
  candidates: null,
  selected: null,
  processed: null,
  report_articles: null,
};

export const PIPELINE_ALREADY_RUNNING = 'PIPELINE_ALREADY_RUNNING';

const DEFAULT_PIPELINE_STATUS: PipelineStatus = {
  running: false,
  last_run: null,
  error: null,
  last_outcome: null,
  progress: { ...DEFAULT_PIPELINE_PROGRESS },
};

export const useDigestStore = defineStore('digest', () => {
  const dateList = ref<DateList>({ dates: [], latest: null });
  const currentDigest = ref<DailyDigest | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const digestRequestId = ref(0);
  const allTags = ref<string[]>([]);
  const allTagsDate = ref<string | null>(null);
  const pipelineStatus = ref<PipelineStatus>({ ...DEFAULT_PIPELINE_STATUS });
  let pipelinePollTimer: ReturnType<typeof setTimeout> | null = null;

  const getErrorMessage = (err: unknown, fallback: string) => {
    if (err instanceof AxiosError) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string' && detail.trim().length > 0) {
        return detail;
      }
    }
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

  const stopPipelinePolling = () => {
    if (pipelinePollTimer !== null) {
      clearTimeout(pipelinePollTimer);
      pipelinePollTimer = null;
    }
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

  const refreshPipelineStatus = async (): Promise<PipelineStatus> => {
    try {
      pipelineStatus.value = await getPipelineStatus();
    } catch (err: unknown) {
      pipelineStatus.value = {
        ...pipelineStatus.value,
        running: false,
        error: getErrorMessage(err, 'Failed to fetch pipeline status'),
        last_outcome: 'error',
        progress: {
          ...(pipelineStatus.value.progress ?? DEFAULT_PIPELINE_PROGRESS),
          stage: 'error',
          message: getErrorMessage(err, 'Failed to fetch pipeline status'),
        },
      };
    }
    return pipelineStatus.value;
  };

  const triggerPipeline = async (): Promise<PipelineRunResponse> => {
    try {
      const response = await triggerPipelineRequest();
      pipelineStatus.value = {
        ...pipelineStatus.value,
        running: true,
        error: null,
        last_outcome: null,
        progress: {
          ...(pipelineStatus.value.progress ?? DEFAULT_PIPELINE_PROGRESS),
          stage: 'starting',
          message: 'Starting pipeline',
          current: 0,
          total: null,
          candidates: 0,
          selected: 0,
          processed: 0,
          report_articles: null,
        },
      };
      return response;
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 409) {
        await refreshPipelineStatus();
        throw new Error(PIPELINE_ALREADY_RUNNING);
      }
      const message = getErrorMessage(err, 'Failed to start pipeline');
      throw new Error(message);
    }
  };

  const startPipelinePolling = (onSettled?: (status: PipelineStatus) => void | Promise<void>) => {
    stopPipelinePolling();

    const poll = async () => {
      const status = await refreshPipelineStatus();
      if (status.running) {
        pipelinePollTimer = window.setTimeout(() => {
          void poll();
        }, 3000);
        return;
      }

      await fetchDateList();
      if (onSettled) {
        await onSettled(status);
      }
    };

    void poll();
  };

  return {
    dateList,
    currentDigest,
    loading,
    error,
    allTags,
    allTagsDate,
    pipelineStatus,
    clearTagCache,
    fetchDateList,
    fetchDigest,
    refreshPipelineStatus,
    triggerPipeline,
    startPipelinePolling,
    stopPipelinePolling,
  };
});
