export interface DateEntry {
  date: string;
  total: number;
  by_category: Record<string, number>;
}

export interface DateList {
  dates: DateEntry[];
  latest: string | null;
}

export interface Article {
  id: string;
  title: string;
  url: string;
  published: string;
  source_name: string;
  source_category: 'arxiv' | 'news' | 'official' | 'community';
  summary_zh: string;
  tags: string[];
  importance: number;
}

export interface DigestStats {
  total: number;
  by_category: Record<string, number>;
  by_tag: Record<string, number>;
}

export interface DailyDigest {
  date: string;
  generated_at: string;
  stats: DigestStats;
  articles: Article[];
}

export interface PipelineRunResponse {
  status: 'started';
}

export interface PipelineProgress {
  stage: 'starting' | 'fetching' | 'stage1' | 'stage2' | 'finalizing' | 'completed' | 'error' | null;
  message: string | null;
  current: number | null;
  total: number | null;
  candidates: number | null;
  selected: number | null;
  processed: number | null;
  report_articles: number | null;
}

export interface PipelineStatus {
  running: boolean;
  last_run: string | null;
  error: string | null;
  last_outcome?: 'success' | 'no_new_items' | 'error' | null;
  progress?: PipelineProgress | null;
}

export interface QueryParams {
  tags?: string[];
  category?: string;
  min_importance?: number;
  sort?: 'importance' | 'published';
  q?: string;
}

export interface GitHubProject {
  id: string;
  full_name: string;
  description: string | null;
  description_zh: string | null;
  html_url: string;
  homepage: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  language: string | null;
  topics: string[];
  category: string;
  created_at: string | null;
  updated_at: string | null;
  pushed_at: string | null;
  owner_avatar: string | null;
  owner_type: string | null;
  license: string | null;
  stars_today: number | null;
  stars_weekly: number | null;
  trend: 'hot' | 'rising' | 'stable' | null;
}

export interface GitHubTrendingStats {
  total: number;
  by_category: Record<string, number>;
  by_language: Record<string, number>;
}

export interface GitHubTrendingData {
  date: string;
  generated_at: string;
  stats: GitHubTrendingStats;
  projects: GitHubProject[];
}

export interface GitHubDateListResponse {
  dates: string[];
  latest: string | null;
}

export interface GitHubFetchProgress {
  stage: 'starting' | 'searching' | 'deduplicating' | 'computing_trends' | 'saving' | 'completed' | 'error' | null;
  message: string | null;
  current: number | null;
  total: number | null;
  topics_done: number | null;
  topics_total: number | null;
  projects_found: number | null;
  projects_new: number | null;
}

export interface GitHubFetchStatus {
  running: boolean;
  last_run: string | null;
  error: string | null;
  last_outcome: 'success' | 'error' | null;
  progress: GitHubFetchProgress | null;
}

export interface GitHubFetchRunResponse {
  status: 'started';
}

export interface GitHubQueryParams {
  category?: string | null;
  language?: string[] | string | null;
  min_stars?: number;
  sort?: 'stars' | 'stars_today' | 'stars_weekly' | 'updated';
  q?: string | null;
  trend?: 'rising' | 'hot' | 'stable' | null;
}
