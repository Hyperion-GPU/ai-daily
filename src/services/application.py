from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.settings import load_config

from .configuration import DesktopConfigurationService
from .desktop_sync import DesktopArchiveSyncService
from .digest import DigestArchiveService, list_dates as default_list_dates, load_digest as default_load_digest, load_index as default_load_index
from .execution import (
    GitHubExecutionService,
    GitHubTrendingFetcher as default_github_fetcher_factory,
    PipelineExecutionService,
    run_pipeline as default_run_pipeline,
)
from .github_trending import (
    GitHubSnapshotQueryService,
    list_github_dates as default_list_github_dates,
    load_github_trending as default_load_github_trending,
)


@dataclass
class ApplicationServices:
    config: dict | None = None
    load_config_fn: Callable[..., dict] = load_config
    list_dates_fn: Callable[[dict | None], list[str]] | None = None
    load_index_fn: Callable[[dict | None], list[dict] | None] | None = None
    load_digest_fn: Callable[[str, dict | None], dict | None] | None = None
    list_github_dates_fn: Callable[[dict | None], list[str]] | None = None
    load_github_trending_fn: Callable[[str, dict | None], dict | None] | None = None
    run_pipeline_fn: Callable[..., object] | None = None
    github_fetcher_factory: Callable[[dict], object] | None = None
    digest_archive_service: DigestArchiveService | None = None
    github_snapshot_service: GitHubSnapshotQueryService | None = None
    pipeline_execution_service: PipelineExecutionService | None = None
    github_execution_service: GitHubExecutionService | None = None
    configuration_service: DesktopConfigurationService | None = None
    desktop_sync_service: DesktopArchiveSyncService | None = None

    def __post_init__(self) -> None:
        self.digest_archive_service = self.digest_archive_service or DigestArchiveService(
            list_dates_fn=self.list_dates_fn or default_list_dates,
            load_index_fn=self.load_index_fn or default_load_index,
            load_digest_fn=self.load_digest_fn or default_load_digest,
        )
        self.github_snapshot_service = self.github_snapshot_service or GitHubSnapshotQueryService(
            list_dates_fn=self.list_github_dates_fn or default_list_github_dates,
            load_github_trending_fn=self.load_github_trending_fn or default_load_github_trending,
        )
        self.pipeline_execution_service = self.pipeline_execution_service or PipelineExecutionService(
            run_pipeline_fn=self.run_pipeline_fn or default_run_pipeline,
        )
        self.github_execution_service = self.github_execution_service or GitHubExecutionService(
            github_fetcher_factory=self.github_fetcher_factory or default_github_fetcher_factory,
        )
        self.configuration_service = self.configuration_service or DesktopConfigurationService()
        self.desktop_sync_service = self.desktop_sync_service or DesktopArchiveSyncService()

    def current_config(self) -> dict:
        if self.config is None:
            self.config = self.load_config_fn()
        return self.config

    def replace_config(self, config: dict) -> None:
        self.config = config

    def get_dates(self) -> dict:
        return self.digest_archive_service.get_dates(self.current_config())

    def get_digest(
        self,
        date: str,
        *,
        tags: list[str],
        category: str | None,
        min_importance: int,
        sort: str,
        q: str | None,
    ) -> dict | None:
        return self.digest_archive_service.get_digest(
            self.current_config(),
            date,
            tags=tags,
            category=category,
            min_importance=min_importance,
            sort=sort,
            q=q,
        )

    def get_github_dates(self) -> dict:
        return self.github_snapshot_service.get_dates(self.current_config())

    def get_latest_github_trending(
        self,
        *,
        category: str | None,
        language: list[str],
        min_stars: int,
        sort: str,
        q: str | None,
        trend: str | None,
    ) -> dict | None:
        return self.github_snapshot_service.get_latest(
            self.current_config(),
            category=category,
            language=language,
            min_stars=min_stars,
            sort=sort,
            q=q,
            trend=trend,
        )

    def get_github_trending_by_date(
        self,
        date: str,
        *,
        category: str | None,
        language: list[str],
        min_stars: int,
        sort: str,
        q: str | None,
        trend: str | None,
    ) -> dict | None:
        return self.github_snapshot_service.get_by_date(
            self.current_config(),
            date,
            category=category,
            language=language,
            min_stars=min_stars,
            sort=sort,
            q=q,
            trend=trend,
        )

    async def run_pipeline_async(self, progress_callback: Callable[[dict], None] | None = None) -> dict:
        return await self.pipeline_execution_service.run(
            self.current_config(),
            progress_callback=progress_callback,
        )

    async def run_github_fetch_async(self, progress_callback: Callable[[dict], None] | None = None) -> dict:
        return await self.github_execution_service.run(
            self.current_config(),
            progress_callback=progress_callback,
        )
