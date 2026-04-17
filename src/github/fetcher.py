import json
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal, TypedDict

import httpx

from src.runtime import get_runtime_paths
from src.settings import get_github_token
from src.utils import now_in_config_timezone, setup_logger

from .categories import resolve_category


class GitHubRateLimitExceeded(RuntimeError):
    pass


class GitHubFetchProgress(TypedDict, total=False):
    stage: Literal["starting", "searching", "deduplicating", "computing_trends", "saving", "completed", "error"]
    message: str
    current: int
    total: int
    topics_done: int
    topics_total: int
    projects_found: int
    projects_new: int


class GitHubTrendingFetcher:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(config)

        github_cfg = config.get("github_trending", {})
        self.enabled = bool(github_cfg.get("enabled", False))
        self.token_env = github_cfg.get("token_env", "GITHUB_TOKEN")
        self.min_stars = int(github_cfg.get("min_stars", 500))
        self.max_projects_per_day = int(github_cfg.get("max_projects_per_day", 50))
        self.per_topic_limit = min(int(github_cfg.get("per_topic_limit", 100)), 100)
        self.topics = [
            topic
            for topic in github_cfg.get("topics", [])
            if isinstance(topic, str) and topic.strip()
        ]
        self.category_map = github_cfg.get("category_map", {})
        self.output_dir = get_runtime_paths(config=config).output_dir
        self.github_output_dir = self.output_dir / "github"
        self.github_output_dir.mkdir(parents=True, exist_ok=True)

    def _emit_progress(
        self,
        progress_callback: Callable[[GitHubFetchProgress], None] | None,
        **payload: object,
    ) -> None:
        if progress_callback is None:
            return
        progress_callback(payload.copy())  # type: ignore[arg-type]

    def _snapshot_path(self, date_str: str) -> Path:
        return self.github_output_dir / f"trending-{date_str}.json"

    def _partial_snapshot_path(self, date_str: str) -> Path:
        return self.github_output_dir / f"trending-{date_str}.partial.json"

    def _list_snapshot_dates(self) -> list[str]:
        dates: list[str] = []
        for path in self.github_output_dir.glob("trending-*.json"):
            prefix = "trending-"
            if not path.stem.startswith(prefix):
                continue
            date_str = path.stem[len(prefix):]
            try:
                date.fromisoformat(date_str)
            except ValueError:
                continue
            dates.append(date_str)
        return sorted(dates, reverse=True)

    def _load_snapshot(self, date_str: str) -> dict | None:
        path = self._snapshot_path(date_str)
        if not path.exists():
            return None

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.logger.warning(f"Failed to read GitHub snapshot: {path}")
            return None

    def _load_snapshot_on_or_before(self, target_date: date, *, strict_before: bool) -> dict | None:
        for date_str in self._list_snapshot_dates():
            snapshot_date = date.fromisoformat(date_str)
            if strict_before and snapshot_date >= target_date:
                continue
            if not strict_before and snapshot_date > target_date:
                continue
            snapshot = self._load_snapshot(date_str)
            if snapshot is not None:
                return snapshot
        return None

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AI-Daily-GitHub-Trending/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = get_github_token(self.config) if self.token_env else None
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _current_token(self) -> str | None:
        return get_github_token(self.config) if self.token_env else None

    def _normalize_project(self, item: dict) -> dict:
        topics = item.get("topics") if isinstance(item.get("topics"), list) else []
        return {
            "id": item.get("full_name"),
            "full_name": item.get("full_name"),
            "description": item.get("description"),
            "description_zh": None,
            "html_url": item.get("html_url"),
            "homepage": item.get("homepage"),
            "stars": int(item.get("stargazers_count", 0) or 0),
            "forks": int(item.get("forks_count", 0) or 0),
            "open_issues": int(item.get("open_issues_count", 0) or 0),
            "language": item.get("language"),
            "topics": topics,
            "category": resolve_category(topics, self.category_map),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "pushed_at": item.get("pushed_at"),
            "owner_avatar": (item.get("owner") or {}).get("avatar_url"),
            "owner_type": (item.get("owner") or {}).get("type"),
            "license": ((item.get("license") or {}).get("spdx_id") or None),
            "stars_today": None,
            "stars_weekly": None,
            "trend": None,
        }

    async def _search_topic(self, client: httpx.AsyncClient, topic: str) -> list[dict]:
        query = f"topic:{topic} stars:>={self.min_stars} archived:false mirror:false"
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": self.per_topic_limit,
                "page": 1,
            },
            timeout=30.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                payload = response.json()
                detail = str(payload.get("message") or "")
            except (ValueError, TypeError, AttributeError):
                detail = response.text

            is_rate_limited = (
                response.status_code == 403
                and "rate limit" in detail.casefold()
            )
            if is_rate_limited:
                raise GitHubRateLimitExceeded(detail or "GitHub API rate limit exceeded") from exc
            raise
        payload = response.json()
        items = payload.get("items", [])
        if not isinstance(items, list):
            return []
        return [self._normalize_project(item) for item in items if isinstance(item, dict)]

    def _merge_projects(self, existing: list[dict], incoming: list[dict]) -> list[dict]:
        merged: dict[str, dict] = {}

        for project in existing:
            project_id = project.get("id")
            if isinstance(project_id, str) and project_id:
                merged[project_id] = dict(project)

        for project in incoming:
            project_id = project.get("id")
            if not isinstance(project_id, str) or not project_id:
                continue

            previous = merged.get(project_id, {})
            combined = dict(previous)
            combined.update(project)
            if combined.get("description_zh") is None and previous.get("description_zh"):
                combined["description_zh"] = previous["description_zh"]
            merged[project_id] = combined

        return list(merged.values())

    def _build_stats(self, projects: list[dict]) -> dict:
        by_category = Counter(
            project.get("category")
            for project in projects
            if isinstance(project.get("category"), str) and project.get("category")
        )
        by_language = Counter(
            project.get("language")
            for project in projects
            if isinstance(project.get("language"), str) and project.get("language")
        )
        return {
            "total": len(projects),
            "by_category": dict(by_category),
            "by_language": dict(by_language),
        }

    def _apply_trends(
        self,
        projects: list[dict],
        previous_snapshot: dict | None,
        weekly_snapshot: dict | None,
    ) -> list[dict]:
        previous_by_id = {
            project.get("id"): project
            for project in (previous_snapshot or {}).get("projects", [])
            if isinstance(project, dict) and isinstance(project.get("id"), str)
        }
        weekly_by_id = {
            project.get("id"): project
            for project in (weekly_snapshot or {}).get("projects", [])
            if isinstance(project, dict) and isinstance(project.get("id"), str)
        }

        enriched: list[dict] = []
        for project in projects:
            project_id = project.get("id")
            current_stars = int(project.get("stars", 0) or 0)

            previous_project = previous_by_id.get(project_id)
            weekly_project = weekly_by_id.get(project_id)

            stars_today = None
            if previous_project is not None:
                stars_today = current_stars - int(previous_project.get("stars", 0) or 0)

            stars_weekly = None
            if weekly_project is not None:
                stars_weekly = current_stars - int(weekly_project.get("stars", 0) or 0)

            trend = None
            if stars_weekly is not None:
                if stars_weekly > 500:
                    trend = "hot"
                elif stars_weekly > 100:
                    trend = "rising"
                else:
                    trend = "stable"

            enriched_project = dict(project)
            enriched_project["stars_today"] = stars_today
            enriched_project["stars_weekly"] = stars_weekly
            enriched_project["trend"] = trend
            enriched.append(enriched_project)

        return enriched

    @staticmethod
    def _sort_projects(projects: list[dict]) -> list[dict]:
        def sort_key(project: dict) -> tuple[int, str]:
            return int(project.get("stars", 0) or 0), str(project.get("updated_at") or "")

        return sorted(projects, key=sort_key, reverse=True)

    def _build_snapshot_payload(
        self,
        *,
        date_str: str,
        generated_at: datetime,
        projects: list[dict],
    ) -> dict:
        return {
            "date": date_str,
            "generated_at": generated_at.isoformat(),
            "stats": self._build_stats(projects),
            "projects": projects,
        }

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _remove_partial_snapshot(self, date_str: str) -> None:
        path = self._partial_snapshot_path(date_str)
        if path.exists():
            path.unlink()

    def _build_degraded_result(
        self,
        *,
        date_str: str,
        generated_at: datetime,
        reason: Literal["missing_token", "rate_limit"],
        progress_callback: Callable[[GitHubFetchProgress], None] | None,
        message: str,
        projects: list[dict],
        projects_found: int,
        projects_new: int,
        topics_done: int,
        topics_total: int,
    ) -> dict:
        payload = self._build_snapshot_payload(
            date_str=date_str,
            generated_at=generated_at,
            projects=projects,
        )
        payload["outcome"] = "degraded"
        payload["reason"] = reason

        partial_path = self._partial_snapshot_path(date_str)
        self._emit_progress(
            progress_callback,
            stage="saving",
            message=message,
            current=topics_done,
            total=topics_total,
            topics_done=topics_done,
            topics_total=topics_total,
            projects_found=projects_found,
            projects_new=projects_new,
        )
        self._write_json(partial_path, payload)
        self.logger.warning("Saved degraded GitHub snapshot: %s", partial_path)
        self._emit_progress(
            progress_callback,
            stage="completed",
            message=message,
            current=topics_done,
            total=topics_total,
            topics_done=topics_done,
            topics_total=topics_total,
            projects_found=projects_found,
            projects_new=projects_new,
        )
        return {
            "outcome": "degraded",
            "reason": reason,
            "snapshot": None,
            "partial_path": str(partial_path),
        }

    async def run(
        self,
        progress_callback: Callable[[GitHubFetchProgress], None] | None = None,
        now: datetime | None = None,
    ) -> dict:
        if not self.enabled:
            raise RuntimeError("GitHub trending fetch is disabled")
        if not self.topics:
            raise RuntimeError("No GitHub trending topics configured")

        generated_at = now or now_in_config_timezone(self.config)
        date_str = generated_at.date().isoformat()
        topics_total = len(self.topics)
        official_today_snapshot = self._load_snapshot(date_str)
        official_today_projects = list((official_today_snapshot or {}).get("projects", []))
        existing_ids = {
            project.get("id")
            for project in official_today_projects
            if isinstance(project, dict) and isinstance(project.get("id"), str)
        }

        self._emit_progress(
            progress_callback,
            stage="starting",
            message="Initializing GitHub trending fetch",
            current=0,
            total=topics_total,
            topics_done=0,
            topics_total=topics_total,
            projects_found=0,
            projects_new=0,
        )

        projects_found = 0
        projects_new = 0
        discovered_ids: set[str] = set()
        fetched_projects: list[dict] = []

        token = self._current_token()
        if not token:
            self.logger.warning("GitHub token missing; skipping anonymous GitHub trending fetch.")
            return self._build_degraded_result(
                date_str=date_str,
                generated_at=generated_at,
                reason="missing_token",
                progress_callback=progress_callback,
                message="GitHub fetch degraded: missing GITHUB_TOKEN; no official snapshot written.",
                projects=[],
                projects_found=0,
                projects_new=0,
                topics_done=0,
                topics_total=topics_total,
            )

        async with httpx.AsyncClient(headers=self._build_headers()) as client:
            for index, topic in enumerate(self.topics, start=1):
                self._emit_progress(
                    progress_callback,
                    stage="searching",
                    message=f"Searching topic: {topic}",
                    current=index - 1,
                    total=topics_total,
                    topics_done=index - 1,
                    topics_total=topics_total,
                    projects_found=projects_found,
                    projects_new=projects_new,
                )

                try:
                    topic_projects = await self._search_topic(client, topic)
                except GitHubRateLimitExceeded as exc:
                    self.logger.warning(
                        "GitHub rate limit reached after %s/%s topics. Saving degraded snapshot.",
                        index - 1,
                        topics_total,
                    )
                    partial_projects = self._apply_trends(
                        fetched_projects,
                        self._load_snapshot_on_or_before(generated_at.date(), strict_before=True),
                        self._load_snapshot_on_or_before(
                            generated_at.date() - timedelta(days=7),
                            strict_before=False,
                        ),
                    )
                    partial_projects = self._sort_projects(partial_projects)[: self.max_projects_per_day]
                    return self._build_degraded_result(
                        date_str=date_str,
                        generated_at=generated_at,
                        reason="rate_limit",
                        progress_callback=progress_callback,
                        message="GitHub fetch degraded: rate limit reached; existing official snapshot kept.",
                        projects=partial_projects,
                        projects_found=projects_found,
                        projects_new=projects_new,
                        topics_done=index - 1,
                        topics_total=topics_total,
                    )
                projects_found += len(topic_projects)

                unseen_ids = {
                    project.get("id")
                    for project in topic_projects
                    if isinstance(project.get("id"), str)
                    and project.get("id") not in discovered_ids
                    and project.get("id") not in existing_ids
                }
                projects_new += len(unseen_ids)
                discovered_ids.update(
                    project.get("id")
                    for project in topic_projects
                    if isinstance(project.get("id"), str)
                )
                fetched_projects = self._merge_projects(fetched_projects, topic_projects)

                self._emit_progress(
                    progress_callback,
                    stage="searching",
                    message=f"Searching topic: {topic}",
                    current=index,
                    total=topics_total,
                    topics_done=index,
                    topics_total=topics_total,
                    projects_found=projects_found,
                    projects_new=projects_new,
                )

        self._emit_progress(
            progress_callback,
            stage="deduplicating",
            message="Deduplicating repositories",
            current=topics_total,
            total=topics_total,
            topics_done=topics_total,
            topics_total=topics_total,
            projects_found=projects_found,
            projects_new=projects_new,
        )

        previous_snapshot = self._load_snapshot_on_or_before(generated_at.date(), strict_before=True)
        weekly_snapshot = self._load_snapshot_on_or_before(
            generated_at.date() - timedelta(days=7),
            strict_before=False,
        )

        self._emit_progress(
            progress_callback,
            stage="computing_trends",
            message="Computing trend deltas",
            current=topics_total,
            total=topics_total,
            topics_done=topics_total,
            topics_total=topics_total,
            projects_found=projects_found,
            projects_new=projects_new,
        )

        merged_projects = self._merge_projects(official_today_projects, fetched_projects)
        projects = self._apply_trends(merged_projects, previous_snapshot, weekly_snapshot)
        projects = self._sort_projects(projects)[: self.max_projects_per_day]
        payload = self._build_snapshot_payload(
            date_str=date_str,
            generated_at=generated_at,
            projects=projects,
        )

        self._emit_progress(
            progress_callback,
            stage="saving",
            message="Saving GitHub trending snapshot",
            current=topics_total,
            total=topics_total,
            topics_done=topics_total,
            topics_total=topics_total,
            projects_found=projects_found,
            projects_new=projects_new,
        )

        path = self._snapshot_path(date_str)
        self._write_json(path, payload)
        self._remove_partial_snapshot(date_str)
        self.logger.info(f"Saved GitHub trending snapshot: {path}")

        self._emit_progress(
            progress_callback,
            stage="completed",
            message="GitHub trending snapshot is ready",
            current=topics_total,
            total=topics_total,
            topics_done=topics_total,
            topics_total=topics_total,
            projects_found=projects_found,
            projects_new=projects_new,
        )
        return {
            "outcome": "success",
            "reason": None,
            "snapshot": payload,
            "partial_path": None,
        }
