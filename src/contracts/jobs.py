from typing import Literal

from pydantic import BaseModel


class PipelineRunResponse(BaseModel):
    status: Literal["started"]


class PipelineProgressResponse(BaseModel):
    stage: Literal["starting", "fetching", "stage1", "stage2", "finalizing", "completed", "error"] | None
    message: str | None
    current: int | None
    total: int | None
    candidates: int | None
    selected: int | None
    processed: int | None
    report_articles: int | None


class PipelineStatusResponse(BaseModel):
    running: bool
    last_run: str | None
    error: str | None
    last_outcome: Literal["success", "no_new_items", "error"] | None
    progress: PipelineProgressResponse | None


class GitHubFetchRunResponse(BaseModel):
    status: Literal["started"]


class GitHubFetchProgressResponse(BaseModel):
    stage: Literal["starting", "searching", "deduplicating", "computing_trends", "saving", "completed", "error"] | None
    message: str | None
    current: int | None
    total: int | None
    topics_done: int | None
    topics_total: int | None
    projects_found: int | None
    projects_new: int | None


class GitHubFetchStatusResponse(BaseModel):
    running: bool
    last_run: str | None
    error: str | None
    last_outcome: Literal["success", "degraded", "error"] | None
    progress: GitHubFetchProgressResponse | None
