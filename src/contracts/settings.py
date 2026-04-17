from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LlmProviderSettings(BaseModel):
    base_url: str = ""
    model: str = ""
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1500, ge=1)


class LlmSettings(BaseModel):
    provider: Literal["siliconflow", "newapi"] = "siliconflow"
    siliconflow: LlmProviderSettings = Field(default_factory=LlmProviderSettings)
    newapi: LlmProviderSettings = Field(default_factory=LlmProviderSettings)


class PipelineSettings(BaseModel):
    time_window_hours: int = Field(default=48, ge=1)
    max_articles_per_day: int = Field(default=30, ge=1)
    max_articles_to_stage2: int = Field(default=50, ge=1)
    stage1_batch_size: int = Field(default=50, ge=1)


class GitHubTrendingSettings(BaseModel):
    enabled: bool = False
    min_stars: int = Field(default=500, ge=0)
    max_projects_per_day: int = Field(default=50, ge=1)


class DesktopSettingsSnapshot(BaseModel):
    timezone: str = "Asia/Shanghai"
    llm: LlmSettings = Field(default_factory=LlmSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    github_trending: GitHubTrendingSettings = Field(default_factory=GitHubTrendingSettings)
    llm_api_key: str = ""
    github_token: str = ""


class ValidationIssue(BaseModel):
    field: str | None = None
    message: str


class ValidationResult(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
