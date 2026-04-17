from __future__ import annotations

from collections.abc import Callable
from typing import Any

from main import run_pipeline
from src.github import GitHubTrendingFetcher

RunPipelineFn = Callable[..., Any]


class PipelineExecutionService:
    def __init__(self, *, run_pipeline_fn: RunPipelineFn = run_pipeline) -> None:
        self._run_pipeline_fn = run_pipeline_fn

    async def run(self, config: dict, progress_callback: Callable[[dict], None] | None = None) -> dict:
        return await self._run_pipeline_fn(config, progress_callback=progress_callback)


class GitHubExecutionService:
    def __init__(
        self,
        *,
        github_fetcher_factory: Callable[[dict], GitHubTrendingFetcher] = GitHubTrendingFetcher,
    ) -> None:
        self._github_fetcher_factory = github_fetcher_factory

    async def run(self, config: dict, progress_callback: Callable[[dict], None] | None = None) -> dict:
        fetcher = self._github_fetcher_factory(config)
        return await fetcher.run(progress_callback=progress_callback)
