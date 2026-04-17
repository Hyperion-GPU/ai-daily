from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone

from dateutil import parser as date_parser

from src.server.loader import list_github_dates, load_github_trending

LoadDigestFn = Callable[[str, dict | None], dict | None]
ListDatesFn = Callable[[dict | None], list[str]]


def updated_sort_key(project: dict) -> datetime:
    updated = project.get("updated_at")
    if not updated:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        parsed = date_parser.parse(str(updated))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sort_metric_value(project: dict, key: str) -> int:
    value = project.get(key)
    return int(value) if value is not None else -1


class GitHubSnapshotQueryService:
    def __init__(
        self,
        *,
        list_dates_fn: ListDatesFn = list_github_dates,
        load_github_trending_fn: LoadDigestFn = load_github_trending,
    ) -> None:
        self._list_dates_fn = list_dates_fn
        self._load_github_trending_fn = load_github_trending_fn

    def get_dates(self, config: dict) -> dict:
        date_strings = self._list_dates_fn(config)
        return {"dates": date_strings, "latest": date_strings[0] if date_strings else None}

    def get_latest(
        self,
        config: dict,
        *,
        category: str | None,
        language: list[str],
        min_stars: int,
        sort: str,
        q: str | None,
        trend: str | None,
    ) -> dict | None:
        dates = self._list_dates_fn(config)
        if not dates:
            return None
        return self.get_by_date(
            config,
            dates[0],
            category=category,
            language=language,
            min_stars=min_stars,
            sort=sort,
            q=q,
            trend=trend,
        )

    def get_by_date(
        self,
        config: dict,
        date: str,
        *,
        category: str | None,
        language: list[str],
        min_stars: int,
        sort: str,
        q: str | None,
        trend: str | None,
    ) -> dict | None:
        data = self._load_github_trending_fn(date, config)
        if data is None:
            return None

        projects = list(data.get("projects", []))

        if category:
            projects = [project for project in projects if project.get("category") == category]
        if language:
            normalized_languages = {item.casefold() for item in language}
            projects = [
                project
                for project in projects
                if isinstance(project.get("language"), str)
                and project["language"].casefold() in normalized_languages
            ]
        if min_stars > 0:
            projects = [project for project in projects if int(project.get("stars", 0) or 0) >= min_stars]
        if trend:
            projects = [project for project in projects if project.get("trend") == trend]
        if q:
            q_normalized = q.casefold()
            projects = [
                project
                for project in projects
                if q_normalized in str(project.get("full_name", "")).casefold()
                or q_normalized in str(project.get("description", "")).casefold()
                or q_normalized in str(project.get("description_zh", "")).casefold()
            ]

        if sort == "updated":
            projects = sorted(projects, key=updated_sort_key, reverse=True)
        elif sort == "stars_today":
            projects = sorted(projects, key=lambda project: sort_metric_value(project, "stars_today"), reverse=True)
        elif sort == "stars_weekly":
            projects = sorted(projects, key=lambda project: sort_metric_value(project, "stars_weekly"), reverse=True)
        else:
            projects = sorted(projects, key=lambda project: int(project.get("stars", 0) or 0), reverse=True)

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
            "date": data["date"],
            "generated_at": data["generated_at"],
            "stats": {
                "total": len(projects),
                "by_category": dict(by_category),
                "by_language": dict(by_language),
            },
            "projects": projects,
        }
