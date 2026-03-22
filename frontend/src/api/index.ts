import axios from 'axios';
import type {
  DateList,
  DailyDigest,
  PipelineRunResponse,
  PipelineStatus,
  QueryParams,
  GitHubDateListResponse,
  GitHubTrendingData,
  GitHubFetchRunResponse,
  GitHubFetchStatus,
  GitHubQueryParams,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

const ensureGithubTrendingData = (payload: unknown): GitHubTrendingData => {
  if (
    !isRecord(payload) ||
    typeof payload.date !== 'string' ||
    typeof payload.generated_at !== 'string' ||
    !Array.isArray(payload.projects) ||
    !isRecord(payload.stats) ||
    typeof payload.stats.total !== 'number' ||
    !isRecord(payload.stats.by_category) ||
    !isRecord(payload.stats.by_language)
  ) {
    throw new Error('Invalid GitHub trending response');
  }

  return payload as unknown as GitHubTrendingData;
};

export const getDates = async (): Promise<DateList> => {
  const { data } = await api.get<DateList>('/dates');
  return data;
};

export const getDigest = async (date: string, params: QueryParams = {}): Promise<DailyDigest> => {
  const { data } = await api.get<DailyDigest>(`/digest/${date}`, { params });
  return data;
};

export const triggerPipeline = async (): Promise<PipelineRunResponse> => {
  const { data } = await api.post<PipelineRunResponse>('/pipeline/run');
  return data;
};

export const getPipelineStatus = async (): Promise<PipelineStatus> => {
  const { data } = await api.get<PipelineStatus>('/pipeline/status');
  return data;
};

export const getGithubDates = async (): Promise<GitHubDateListResponse> => {
  const { data } = await api.get<GitHubDateListResponse>('/github/dates');
  return data;
};

export const getGithubTrending = async (date?: string, params: GitHubQueryParams = {}): Promise<GitHubTrendingData> => {
  const url = date && date !== 'latest' ? `/github/trending/${date}` : '/github/trending';
  const { data } = await api.get<GitHubTrendingData>(url, { params });
  return ensureGithubTrendingData(data);
};

export const triggerGithubFetch = async (): Promise<GitHubFetchRunResponse> => {
  const { data } = await api.post<GitHubFetchRunResponse>('/github/fetch');
  return data;
};

export const getGithubFetchStatus = async (): Promise<GitHubFetchStatus> => {
  const { data } = await api.get<GitHubFetchStatus>('/github/fetch/status');
  return data;
};

export default api;
