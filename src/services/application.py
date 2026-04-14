from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as date_parser

from main import run_pipeline
from src.github import GitHubTrendingFetcher
from src.server.loader import list_dates, list_github_dates, load_digest, load_github_trending, load_index
from src.settings import load_config

LoadDigestFn = Callable[[str, dict | None], dict | None]
LoadIndexFn = Callable[[dict | None], list[dict] | None]
ListDatesFn = Callable[[dict | None], list[str]]
RunPipelineFn = Callable[..., Any]


def _published_sort_key(article: dict) -> datetime:
    published = article.get("published")
    if not published:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        parsed = date_parser.parse(str(published))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _updated_sort_key(project: dict) -> datetime:
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


def _sort_metric_value(project: dict, key: str) -> int:
    value = project.get(key)
    return int(value) if value is not None else -1


@dataclass
class ApplicationServices:
    config: dict | None = None
    list_dates_fn: ListDatesFn = list_dates
    load_index_fn: LoadIndexFn = load_index
    load_digest_fn: LoadDigestFn = load_digest
    list_github_dates_fn: ListDatesFn = list_github_dates
    load_github_trending_fn: LoadDigestFn = load_github_trending
    load_config_fn: Callable[..., dict] = load_config
    run_pipeline_fn: RunPipelineFn = run_pipeline
    github_fetcher_factory: Callable[[dict], GitHubTrendingFetcher] = GitHubTrendingFetcher

    def current_config(self) -> dict:
        if self.config is None:
            self.config = self.load_config_fn()
        return self.config

    def replace_config(self, config: dict) -> None:
        self.config = config

    def get_dates(self) -> dict:
        config = self.current_config()
        date_strings = self.list_dates_fn(config)
        index_entries = self.load_index_fn(config) or []
        stats_by_date = {
            entry.get("date"): entry
            for entry in index_entries
            if isinstance(entry.get("date"), str)
        }
        dates = []
        for date in date_strings:
            index_entry = stats_by_date.get(date)
            if index_entry:
                total = index_entry.get("total", 0)
                by_category = index_entry.get("by_category", {})
            else:
                digest = self.load_digest_fn(date, config)
                stats = digest.get("stats", {}) if digest else {}
                total = stats.get("total", 0)
                by_category = stats.get("by_category", {})
            dates.append(
                {
                    "date": date,
                    "total": total,
                    "by_category": by_category,
                }
            )
        return {"dates": dates, "latest": date_strings[0] if date_strings else None}

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
        config = self.current_config()
        data = self.load_digest_fn(date, config)
        if data is None:
            return None

        articles = data["articles"]

        if tags:
            articles = [article for article in articles if any(tag in article["tags"] for tag in tags)]
        if category:
            articles = [article for article in articles if article["source_category"] == category]
        if min_importance > 1:
            articles = [article for article in articles if article["importance"] >= min_importance]
        if q:
            q_normalized = q.casefold()
            articles = [
                article
                for article in articles
                if q_normalized in str(article.get("title", "")).casefold()
                or q_normalized in str(article.get("summary_zh", "")).casefold()
            ]

        if sort == "published":
            articles = sorted(articles, key=_published_sort_key, reverse=True)
        else:
            articles = sorted(articles, key=lambda article: article.get("importance", 0), reverse=True)

        by_category = Counter(article["source_category"] for article in articles)
        by_tag = Counter(tag for article in articles for tag in article["tags"])

        return {
            "date": data["date"],
            "generated_at": data["generated_at"],
            "stats": {
                "total": len(articles),
                "by_category": dict(by_category),
                "by_tag": dict(by_tag),
            },
            "articles": articles,
        }

    def get_github_dates(self) -> dict:
        config = self.current_config()
        date_strings = self.list_github_dates_fn(config)
        return {"dates": date_strings, "latest": date_strings[0] if date_strings else None}

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
        config = self.current_config()
        dates = self.list_github_dates_fn(config)
        if not dates:
            return None
        return self.get_github_trending_by_date(
            dates[0],
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
        config = self.current_config()
        data = self.load_github_trending_fn(date, config)
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
            projects = sorted(projects, key=_updated_sort_key, reverse=True)
        elif sort == "stars_today":
            projects = sorted(projects, key=lambda project: _sort_metric_value(project, "stars_today"), reverse=True)
        elif sort == "stars_weekly":
            projects = sorted(projects, key=lambda project: _sort_metric_value(project, "stars_weekly"), reverse=True)
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

    async def run_pipeline_async(self, progress_callback: Callable[[dict], None] | None = None) -> dict:
        config = self.current_config()
        return await self.run_pipeline_fn(config, progress_callback=progress_callback)

    async def run_github_fetch_async(self, progress_callback: Callable[[dict], None] | None = None) -> dict:
        config = self.current_config()
        fetcher = self.github_fetcher_factory(config)
        return await fetcher.run(progress_callback=progress_callback)
