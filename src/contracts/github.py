from typing import Literal

from pydantic import BaseModel, Field


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


class GitHubFetchResult(BaseModel):
    outcome: Literal["success", "degraded"]
    reason: Literal["missing_token", "rate_limit"] | None = None
    snapshot: GitHubTrendingResponse | None = None
    partial_path: str | None = None


class GitHubDateListResponse(BaseModel):
    dates: list[str]
    latest: str | None = None


class GitHubQueryParams(BaseModel):
    category: str | None = None
    language: list[str] | str | None = Field(default_factory=list)
    min_stars: int = Field(default=0, ge=0)
    sort: Literal["stars", "stars_today", "stars_weekly", "updated"] = "stars"
    q: str | None = None
    trend: Literal["rising", "hot", "stable"] | None = None
