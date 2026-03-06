from pydantic import BaseModel
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


class DateListResponse(BaseModel):
    dates: list[str]
    latest: str | None
