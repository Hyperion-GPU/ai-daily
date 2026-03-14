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

export interface QueryParams {
  tags?: string[];
  category?: string;
  min_importance?: number;
  sort?: 'importance' | 'published';
  q?: string;
}
