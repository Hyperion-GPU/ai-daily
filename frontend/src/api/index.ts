import axios from 'axios';
import type { DateList, DailyDigest, QueryParams } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

export const getDates = async (): Promise<DateList> => {
  const { data } = await api.get<DateList>('/dates');
  return data;
};

export const getDigest = async (date: string, params: QueryParams = {}): Promise<DailyDigest> => {
  const { data } = await api.get<DailyDigest>(`/digest/${date}`, { params });
  return data;
};

export default api;
