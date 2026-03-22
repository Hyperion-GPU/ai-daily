import { AxiosError } from 'axios';
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type {
  GitHubDateListResponse,
  GitHubTrendingData,
  GitHubFetchProgress,
  GitHubFetchRunResponse,
  GitHubFetchStatus,
  GitHubQueryParams
} from '../types';
import {
  getGithubDates,
  getGithubTrending,
  getGithubFetchStatus,
  triggerGithubFetch as triggerGithubFetchRequest
} from '../api';

const DEFAULT_FETCH_PROGRESS: GitHubFetchProgress = {
  stage: null,
  message: null,
  current: null,
  total: null,
  topics_done: null,
  topics_total: null,
  projects_found: null,
  projects_new: null,
};

export const GITHUB_FETCH_ALREADY_RUNNING = 'GITHUB_FETCH_ALREADY_RUNNING';

const DEFAULT_FETCH_STATUS: GitHubFetchStatus = {
  running: false,
  last_run: null,
  error: null,
  last_outcome: null,
  progress: { ...DEFAULT_FETCH_PROGRESS },
};

export const useGithubStore = defineStore('github', () => {
  const dateList = ref<GitHubDateListResponse>({ dates: [], latest: null });
  const currentTrending = ref<GitHubTrendingData | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const trendingRequestId = ref(0);
  const fetchStatus = ref<GitHubFetchStatus>({ ...DEFAULT_FETCH_STATUS });
  let fetchPollTimer: ReturnType<typeof setTimeout> | null = null;

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

  const stopFetchPolling = () => {
    if (fetchPollTimer !== null) {
      clearTimeout(fetchPollTimer);
      fetchPollTimer = null;
    }
  };

  const fetchDateList = async () => {
    loading.value = true;
    error.value = null;
    try {
      dateList.value = await getGithubDates();
    } catch (err: unknown) {
      error.value = getErrorMessage(err, 'Failed to fetch GitHub dates');
    } finally {
      loading.value = false;
    }
  };

  const fetchTrending = async (date?: string, params: GitHubQueryParams = {}) => {
    const requestId = ++trendingRequestId.value;
    loading.value = true;
    error.value = null;
    try {
      const trending = await getGithubTrending(date, params);
      if (requestId !== trendingRequestId.value) {
        return;
      }
      currentTrending.value = trending;
    } catch (err: unknown) {
      if (requestId !== trendingRequestId.value) {
        return;
      }
      error.value = getErrorMessage(err, 'Failed to fetch GitHub trending data');
    } finally {
      if (requestId === trendingRequestId.value) {
        loading.value = false;
      }
    }
  };

  const refreshFetchStatus = async (): Promise<GitHubFetchStatus> => {
    try {
      fetchStatus.value = await getGithubFetchStatus();
    } catch (err: unknown) {
      fetchStatus.value = {
        ...fetchStatus.value,
        running: false,
        error: getErrorMessage(err, 'Failed to fetch GitHub parsing status'),
        last_outcome: 'error',
        progress: {
          ...(fetchStatus.value.progress ?? DEFAULT_FETCH_PROGRESS),
          stage: 'error',
          message: getErrorMessage(err, 'Failed to fetch GitHub parsing status'),
        },
      };
    }
    return fetchStatus.value;
  };

  const triggerFetch = async (): Promise<GitHubFetchRunResponse> => {
    try {
      const response = await triggerGithubFetchRequest();
      fetchStatus.value = {
        ...fetchStatus.value,
        running: true,
        error: null,
        last_outcome: null,
        progress: {
          ...(fetchStatus.value.progress ?? DEFAULT_FETCH_PROGRESS),
          stage: 'starting',
          message: 'Starting GitHub fetching',
        },
      };
      return response;
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.status === 409) {
        await refreshFetchStatus();
        throw new Error(GITHUB_FETCH_ALREADY_RUNNING);
      }
      const message = getErrorMessage(err, 'Failed to start GitHub fetching');
      throw new Error(message);
    }
  };

  const startFetchPolling = (onSettled?: (status: GitHubFetchStatus) => void | Promise<void>) => {
    stopFetchPolling();

    const poll = async () => {
      let status: GitHubFetchStatus;
      try {
        status = await refreshFetchStatus();
      } catch (err: unknown) {
        fetchStatus.value = {
          ...fetchStatus.value,
          running: false,
          error: getErrorMessage(err, 'Failed to fetch GitHub parsing status'),
          last_outcome: 'error',
        };
        return;
      }

      if (status.running) {
        fetchPollTimer = window.setTimeout(() => {
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
    currentTrending,
    loading,
    error,
    fetchStatus,
    fetchDateList,
    fetchTrending,
    refreshFetchStatus,
    triggerFetch,
    startFetchPolling,
    stopFetchPolling,
  };
});
