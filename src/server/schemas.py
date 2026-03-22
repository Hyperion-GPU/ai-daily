from pydantic import BaseModel, Field
from typing import Literal


class Article(BaseModel):
    id: str
    title: str
    url: str
    published: str
    source_name: str
    source_category: Literal["arxiv", "news", "official", "community"]
    summary_zh: str
    tags: list[str]
    importance: int


class DigestStats(BaseModel):
    total: int
    by_category: dict[str, int]
    by_tag: dict[str, int]


class DigestResponse(BaseModel):
    date: str
    generated_at: str
    stats: DigestStats
    articles: list[Article]


class DateEntry(BaseModel):
    date: str
    total: int
    by_category: dict[str, int]


class DateListResponse(BaseModel):
    dates: list[DateEntry]
    latest: str | None


class PipelineRunResponse(BaseModel):
    status: Literal["started"]


class PipelineProgressResponse(BaseModel):
    stage: Literal["starting", "fetching", "stage1", "stage2", "finalizing", "completed", "error"] | None = None
    message: str | None = None
    current: int | None = None
    total: int | None = None
    candidates: int | None = None
    selected: int | None = None
    processed: int | None = None
    report_articles: int | None = None


class PipelineStatusResponse(BaseModel):
    running: bool
    last_run: str | None
    error: str | None
    last_outcome: Literal["success", "no_new_items", "error"] | None = None
    progress: PipelineProgressResponse | None = None


class GitHubProject(BaseModel):
    id: str = Field(min_length=1)
    full_name: str
    description: str | None = None
    description_zh: str | None = None
    html_url: str
    homepage: str | None = None
    stars: int
    forks: int
    open_issues: int
    language: str | None = None
    topics: list[str]
    category: Literal["llm", "agent", "cv", "nlp", "ml_framework", "mlops", "general"]
    created_at: str | None = None
    updated_at: str | None = None
    pushed_at: str | None = None
    owner_avatar: str | None = None
    owner_type: str | None = None
    license: str | None = None
    stars_today: int | None = None
    stars_weekly: int | None = None
    trend: Literal["hot", "rising", "stable"] | None = None


class GitHubTrendingStats(BaseModel):
    total: int
    by_category: dict[str, int]
    by_language: dict[str, int]


class GitHubTrendingResponse(BaseModel):
    date: str
    generated_at: str
    stats: GitHubTrendingStats
    projects: list[GitHubProject]


class GitHubDateListResponse(BaseModel):
    dates: list[str]
    latest: str | None


class GitHubFetchRunResponse(BaseModel):
    status: Literal["started"]


class GitHubFetchProgressResponse(BaseModel):
    stage: Literal["starting", "searching", "deduplicating", "computing_trends", "saving", "completed", "error"] | None = None
    message: str | None = None
    current: int | None = None
    total: int | None = None
    topics_done: int | None = None
    topics_total: int | None = None
    projects_found: int | None = None
    projects_new: int | None = None


class GitHubFetchStatusResponse(BaseModel):
    running: bool
    last_run: str | None
    error: str | None
    last_outcome: Literal["success", "error"] | None = None
    progress: GitHubFetchProgressResponse | None = None
