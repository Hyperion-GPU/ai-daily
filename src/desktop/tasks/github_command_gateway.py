from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.contracts import GitHubDateListResponse, GitHubFetchResult, GitHubTrendingResponse
from src.services import ApplicationServices


class GithubCommandGateway:
    def __init__(self, services_getter: Callable[[], ApplicationServices]) -> None:
        self._services_getter = services_getter

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    @staticmethod
    def _normalize_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
        filters = dict(filters or {})
        languages = filters.get("selectedLanguages", [])
        if isinstance(languages, str):
            selected_languages = [languages] if languages.strip() else []
        elif isinstance(languages, list):
            selected_languages = [
                str(item).strip()
                for item in languages
                if str(item).strip()
            ]
        else:
            selected_languages = []

        sort_key = str(filters.get("sortKey", "stars") or "stars").strip()
        if sort_key not in {"stars", "stars_today", "stars_weekly", "updated"}:
            sort_key = "stars"

        trend_filter = str(filters.get("trendFilter", "") or "").strip()
        if trend_filter not in {"hot", "rising", "stable"}:
            trend_filter = ""

        return {
            "category": str(filters.get("categoryFilter", "") or "").strip() or None,
            "language": selected_languages,
            "min_stars": max(0, int(filters.get("minStars", 0) or 0)),
            "sort": sort_key,
            "q": str(filters.get("searchQuery", "") or "").strip() or None,
            "trend": trend_filter or None,
        }

    def list_dates(self) -> dict[str, Any]:
        payload = GitHubDateListResponse.model_validate(
            self._services().get_github_dates() or {"dates": [], "latest": None}
        )
        items = [
            {
                "date": date_value,
                "label": date_value,
                "isLatest": date_value == payload.latest,
                "projectCount": None,
                "generatedAt": None,
            }
            for date_value in payload.dates
        ]
        return {"dates": items, "latest": payload.latest}

    def load_snapshot(
        self,
        date: str | None,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        kwargs = self._normalize_filters(filters)
        services = self._services()
        if date:
            payload = services.get_github_trending_by_date(date, **kwargs)
        else:
            payload = services.get_latest_github_trending(**kwargs)
        if payload is None:
            return None
        return self._serialize_snapshot(GitHubTrendingResponse.model_validate(payload))

    async def run_fetch(
        self,
        progress_callback=None,
    ) -> dict[str, Any]:
        payload = await self._services().run_github_fetch_async(progress_callback=progress_callback)
        return self._serialize_fetch_result(GitHubFetchResult.model_validate(payload))

    @staticmethod
    def _serialize_snapshot(snapshot: GitHubTrendingResponse) -> dict[str, Any]:
        return {
            "date": snapshot.date,
            "generatedAt": snapshot.generated_at,
            "stats": {
                "total": snapshot.stats.total,
                "byCategory": dict(snapshot.stats.by_category),
                "byLanguage": dict(snapshot.stats.by_language),
            },
            "projects": [
                {
                    "id": project.id,
                    "fullName": project.full_name,
                    "description": project.description or "",
                    "descriptionZh": project.description_zh or "",
                    "htmlUrl": project.html_url,
                    "language": project.language or "",
                    "category": project.category,
                    "stars": project.stars,
                    "starsToday": project.stars_today,
                    "starsWeekly": project.stars_weekly,
                    "trend": project.trend or "",
                    "updatedAt": project.updated_at or "",
                    "ownerAvatar": project.owner_avatar or "",
                    "topics": list(project.topics),
                    "forks": project.forks,
                    "license": project.license or "",
                }
                for project in snapshot.projects
            ],
        }

    @classmethod
    def _serialize_fetch_result(cls, result: GitHubFetchResult) -> dict[str, Any]:
        return {
            "outcome": result.outcome,
            "reason": result.reason,
            "snapshot": cls._serialize_snapshot(result.snapshot) if result.snapshot is not None else None,
            "partialPath": result.partial_path,
        }
