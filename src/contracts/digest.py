from typing import Literal

from pydantic import BaseModel, Field


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


class DigestQueryParams(BaseModel):
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    min_importance: int = Field(default=1, ge=1, le=5)
    sort: Literal["importance", "published"] = "importance"
    q: str | None = None
