import { computed, ref } from 'vue';

export type AppLocale = 'en' | 'zh';

type LocaleMessages = {
  app: {
    beta: string;
    footer: string;
    digestNav: string;
    githubNav: string;
    skipToContent: string;
  };
  home: {
    pageTitle: string;
    pageDescription: string;
    latest: string;
    articles: string;
    empty: string;
    fetchToday: string;
    fetchRunning: string;
    fetchSuccess: string;
    fetchNoUpdates: string;
    fetchError: string;
    fetchAlreadyRunning: string;
    progressTitle: string;
    progressIdle: string;
    progressStarting: string;
    progressFetching: string;
    progressStage1: string;
    progressStage2: string;
    progressFinalizing: string;
    progressCompleted: string;
    progressError: string;
    progressCandidates: string;
    progressSelected: string;
    progressProcessed: string;
    progressReport: string;
  };
  digest: {
    backToArchive: string;
    generatedAt: string;
    search: string;
    searchPlaceholder: string;
    filters: string;
    category: string;
    categoryPlaceholder: string;
    tags: string;
    tagsPlaceholder: string;
    minimumImportance: string;
    sort: string;
    importance: string;
    published: string;
    visibleResults: string;
    items: string;
    empty: string;
    requestFailed: string;
  };
  article: {
    readSource: string;
  };
  categories: {
    all: string;
    arxiv: string;
    official: string;
    news: string;
    community: string;
  };
  github: {
    pageTitle: string;
    pageDescription: string;
    search: string;
    searchPlaceholder: string;
    category: string;
    language: string;
    minStars: string;
    sort: string;
    sortStars: string;
    sortStarsToday: string;
    sortStarsWeekly: string;
    sortUpdated: string;
    trend: string;
    trendAll: string;
    trendHot: string;
    trendRising: string;
    trendStable: string;
    stars: string;
    forks: string;
    issues: string;
    starsToday: string;
    starsWeekly: string;
    viewProject: string;
    updatedAgo: string;
    categoryAll: string;
    categoryLLM: string;
    categoryAgent: string;
    categoryCV: string;
    categoryNLP: string;
    categoryFramework: string;
    categoryMLOps: string;
    categoryGeneral: string;
    fetchData: string;
    fetchRunning: string;
    fetchAlreadyRunning: string;
    fetchSuccess: string;
    fetchError: string;
    progressTitle: string;
    progressStarting: string;
    progressSearching: string;
    progressDedup: string;
    progressTrends: string;
    progressSaving: string;
    progressCompleted: string;
    progressError: string;
    progressTopics: string;
    progressFound: string;
    progressNew: string;
    visibleResults: string;
    items: string;
    empty: string;
  };
};

const STORAGE_KEY = 'ai-daily-locale';

const MESSAGES: Record<AppLocale, LocaleMessages> = {
  en: {
    app: {
      beta: 'Beta',
      footer: 'Daily AI digest',
      digestNav: 'Digest',
      githubNav: 'GitHub',
      skipToContent: 'Skip to main content',
    },
    home: {
      pageTitle: 'Digest Archive',
      pageDescription: 'Browse generated AI Daily digests by date.',
      latest: 'Latest',
      articles: 'articles',
      empty: 'No digest is available yet.',
      fetchToday: "Fetch today's news",
      fetchRunning: 'Fetching...',
      fetchSuccess: 'Fetch complete.',
      fetchNoUpdates: "No new items were added to today's digest.",
      fetchError: 'Fetch failed',
      fetchAlreadyRunning: 'Already running',
      progressTitle: 'Fetch progress',
      progressIdle: 'Idle',
      progressStarting: 'Starting',
      progressFetching: 'Fetching feeds',
      progressStage1: 'Stage 1 filtering',
      progressStage2: 'Stage 2 summarizing',
      progressFinalizing: 'Finalizing report',
      progressCompleted: 'Completed',
      progressError: 'Failed',
      progressCandidates: 'Candidates',
      progressSelected: 'Selected',
      progressProcessed: 'Processed',
      progressReport: 'In report',
    },
    digest: {
      backToArchive: 'Back to archive',
      generatedAt: 'Generated',
      search: 'Search',
      searchPlaceholder: 'Search title or summary...',
      filters: 'Filters',
      category: 'Category',
      categoryPlaceholder: 'Choose a category',
      tags: 'Tags',
      tagsPlaceholder: 'Choose tags',
      minimumImportance: 'Minimum importance',
      sort: 'Sort',
      importance: 'Importance',
      published: 'Published',
      visibleResults: 'Visible results',
      items: 'items',
      empty: 'No articles match the current filters.',
      requestFailed: 'Digest request failed',
    },
    article: {
      readSource: 'Read source',
    },
    categories: {
      all: 'All',
      arxiv: 'Arxiv papers',
      official: 'Official updates',
      news: 'News coverage',
      community: 'Community',
    },
    github: {
      pageTitle: 'GitHub AI Trending',
      pageDescription: 'Discover the most popular AI open-source projects on GitHub.',
      search: 'Search',
      searchPlaceholder: 'Search project name or description...',
      category: 'Category',
      language: 'Language',
      minStars: 'Minimum Stars',
      sort: 'Sort by',
      sortStars: 'Stars',
      sortStarsToday: 'Today',
      sortStarsWeekly: 'This week',
      sortUpdated: 'Recently updated',
      trend: 'Trend',
      trendAll: 'All',
      trendHot: 'Hot',
      trendRising: 'Rising',
      trendStable: 'Stable',
      stars: 'Stars',
      forks: 'Forks',
      issues: 'Issues',
      starsToday: 'today',
      starsWeekly: 'this week',
      viewProject: 'View project',
      updatedAgo: 'Updated {time} ago',
      categoryAll: 'All',
      categoryLLM: 'LLM',
      categoryAgent: 'AI Agent',
      categoryCV: 'Computer Vision',
      categoryNLP: 'NLP',
      categoryFramework: 'ML Framework',
      categoryMLOps: 'MLOps',
      categoryGeneral: 'General AI',
      fetchData: 'Fetch latest data',
      fetchRunning: 'Fetching...',
      fetchAlreadyRunning: 'Already fetching',
      fetchSuccess: 'Data refreshed.',
      fetchError: 'Fetch failed.',
      progressTitle: 'Fetching GitHub AI project data...',
      progressStarting: 'Initializing...',
      progressSearching: 'Searching',
      progressDedup: 'Deduplicating...',
      progressTrends: 'Computing trends...',
      progressSaving: 'Saving data...',
      progressCompleted: 'Completed',
      progressError: 'Failed',
      progressTopics: 'topics',
      progressFound: 'projects found',
      progressNew: 'new',
      visibleResults: 'Total projects',
      items: 'projects',
      empty: 'No projects match the current filters.',
    },
  },
  zh: {
    app: {
      beta: '测试版',
      footer: '每日 AI 日报',
      digestNav: '日报',
      githubNav: 'GitHub',
      skipToContent: '跳转到主要内容',
    },
    home: {
      pageTitle: '日报归档',
      pageDescription: '按日期浏览已经生成的 AI Daily 日报。',
      latest: '最新',
      articles: '篇',
      empty: '暂时还没有可浏览的日报。',
      fetchToday: '获取今日资讯',
      fetchRunning: '正在获取...',
      fetchSuccess: '获取完成。',
      fetchNoUpdates: '今日没有新增内容。',
      fetchError: '获取失败',
      fetchAlreadyRunning: '正在运行中',
      progressTitle: '获取进度',
      progressIdle: '空闲',
      progressStarting: '正在启动',
      progressFetching: '正在抓取源',
      progressStage1: '第一阶段筛选',
      progressStage2: '第二阶段总结',
      progressFinalizing: '正在生成日报',
      progressCompleted: '已完成',
      progressError: '失败',
      progressCandidates: '候选',
      progressSelected: '入选',
      progressProcessed: '已处理',
      progressReport: '已入日报',
    },
    digest: {
      backToArchive: '返回归档',
      generatedAt: '生成于',
      search: '搜索',
      searchPlaceholder: '搜索标题或摘要...',
      filters: '筛选',
      category: '分类',
      categoryPlaceholder: '选择分类',
      tags: '标签',
      tagsPlaceholder: '选择标签',
      minimumImportance: '最低重要性',
      sort: '排序',
      importance: '重要性',
      published: '发布时间',
      visibleResults: '当前结果',
      items: '篇',
      empty: '当前筛选条件下没有文章。',
      requestFailed: '日报加载失败',
    },
    article: {
      readSource: '阅读原文',
    },
    categories: {
      all: '全部',
      arxiv: 'Arxiv 论文',
      official: '官方动态',
      news: '媒体报道',
      community: '社区',
    },
    github: {
      pageTitle: 'GitHub AI 热门项目',
      pageDescription: '发现 GitHub 上最值得关注的 AI 开源项目。',
      search: '搜索',
      searchPlaceholder: '搜索项目名或描述...',
      category: 'AI 分类',
      language: '编程语言',
      minStars: '最低 Stars',
      sort: '排序',
      sortStars: 'Stars 总数',
      sortStarsToday: '今日增长',
      sortStarsWeekly: '本周增长',
      sortUpdated: '最近更新',
      trend: '趋势',
      trendAll: '全部',
      trendHot: '火热',
      trendRising: '上升中',
      trendStable: '平稳',
      stars: 'Stars',
      forks: 'Forks',
      issues: 'Issues',
      starsToday: '今日',
      starsWeekly: '本周',
      viewProject: '查看项目',
      updatedAgo: '{time}前更新',
      categoryAll: '全部',
      categoryLLM: '大语言模型',
      categoryAgent: 'AI 智能体',
      categoryCV: '计算机视觉',
      categoryNLP: '自然语言处理',
      categoryFramework: 'ML 框架',
      categoryMLOps: 'MLOps',
      categoryGeneral: '通用 AI',
      fetchData: '获取最新数据',
      fetchRunning: '正在获取...',
      fetchAlreadyRunning: '已在获取中',
      fetchSuccess: '数据已刷新。',
      fetchError: '获取失败。',
      progressTitle: '正在获取 GitHub AI 项目数据...',
      progressStarting: '正在初始化...',
      progressSearching: '搜索中',
      progressDedup: '正在去重合并...',
      progressTrends: '正在计算趋势数据...',
      progressSaving: '正在保存数据...',
      progressCompleted: '已完成',
      progressError: '失败',
      progressTopics: '个 topic',
      progressFound: '个项目已发现',
      progressNew: '个为新增',
      visibleResults: '项目总数',
      items: '个项目',
      empty: '当前筛选条件下没有匹配的项目。',
    },
  },
};

const normalizeLocale = (value: string | null): AppLocale => (value === 'zh' ? 'zh' : 'en');

const storedLocale =
  typeof window !== 'undefined' ? normalizeLocale(window.localStorage.getItem(STORAGE_KEY)) : 'en';

const locale = ref<AppLocale>(storedLocale);

const applyDocumentLanguage = (value: AppLocale) => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = value === 'zh' ? 'zh-CN' : 'en';
  }
};

applyDocumentLanguage(locale.value);

export const setLocale = (value: AppLocale) => {
  locale.value = value;
  applyDocumentLanguage(value);
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, value);
  }
};

export const toggleLocale = () => {
  setLocale(locale.value === 'en' ? 'zh' : 'en');
};

export const useLocale = () => {
  const copy = computed(() => MESSAGES[locale.value]);
  const dateTimeLocale = computed(() => (locale.value === 'zh' ? 'zh-CN' : 'en-US'));
  const localeToggleLabel = computed(() => (locale.value === 'en' ? '中文' : 'EN'));

  return {
    locale,
    copy,
    dateTimeLocale,
    localeToggleLabel,
    toggleLocale,
    setLocale,
  };
};
