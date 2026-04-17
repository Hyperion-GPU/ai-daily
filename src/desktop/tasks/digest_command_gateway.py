from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.contracts import DateListResponse, DigestQueryParams, DigestResponse
from src.services import ApplicationServices


_SOURCE_CATEGORY_LABELS = {
    "arxiv": "ArXiv",
    "official": "官方",
    "news": "新闻",
    "community": "社区",
}


class DigestCommandGateway:
    def __init__(self, services_getter: Callable[[], ApplicationServices]) -> None:
        self._services_getter = services_getter

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    @staticmethod
    def _normalize_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
        filters = dict(filters or {})
        raw_tags = filters.get("selectedTags", [])
        if isinstance(raw_tags, str):
            selected_tags = [raw_tags.strip()] if raw_tags.strip() else []
        elif isinstance(raw_tags, list):
            selected_tags = []
            for item in raw_tags:
                normalized = str(item).strip()
                if normalized and normalized not in selected_tags:
                    selected_tags.append(normalized)
        else:
            selected_tags = []

        sort_key = str(filters.get("sortKey", "importance") or "importance").strip()
        if sort_key not in {"importance", "published"}:
            sort_key = "importance"

        query = str(filters.get("searchQuery", "") or "").strip() or None
        category = str(filters.get("categoryFilter", "") or "").strip() or None
        min_importance = int(filters.get("minImportance", 1) or 1)
        min_importance = max(1, min(5, min_importance))

        params = DigestQueryParams(
            tags=selected_tags,
            category=category,
            min_importance=min_importance,
            sort=sort_key,
            q=query,
        )
        return {
            "tags": list(params.tags),
            "category": params.category,
            "min_importance": params.min_importance,
            "sort": params.sort,
            "q": params.q,
        }

    def list_dates(self) -> dict[str, Any]:
        payload = DateListResponse.model_validate(
            self._services().get_dates() or {"dates": [], "latest": None}
        )
        items = [
            {
                "date": entry.date,
                "label": entry.date,
                "articleCount": entry.total,
                "isLatest": entry.date == payload.latest,
            }
            for entry in payload.dates
        ]
        return {"dates": items, "latest": payload.latest}

    def load_snapshot(
        self,
        date: str | None,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not date:
            latest = self.list_dates().get("latest")
            if not latest:
                return None
            date = str(latest)

        kwargs = self._normalize_filters(filters)
        payload = self._services().get_digest(str(date), **kwargs)
        if payload is None:
            return None
        return self._serialize_snapshot(DigestResponse.model_validate(payload))

    async def run_fetch(self, progress_callback=None) -> dict[str, Any]:
        payload = dict(await self._services().run_pipeline_async(progress_callback=progress_callback))
        outcome = str(payload.get("result", "") or "")
        payload["outcome"] = outcome if outcome == "no_new_items" else "success"
        return payload

    @staticmethod
    def _serialize_snapshot(snapshot: DigestResponse) -> dict[str, Any]:
        return {
            "date": snapshot.date,
            "generatedAt": snapshot.generated_at,
            "stats": {
                "total": snapshot.stats.total,
                "byCategory": dict(snapshot.stats.by_category),
                "byTag": dict(snapshot.stats.by_tag),
            },
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "published": article.published,
                    "publishedLabel": _format_published_label(article.published),
                    "sourceName": article.source_name,
                    "sourceCategory": article.source_category,
                    "sourceCategoryLabel": _SOURCE_CATEGORY_LABELS.get(article.source_category, article.source_category),
                    "summaryZh": article.summary_zh,
                    "tags": list(article.tags),
                    "importance": article.importance,
                }
                for article in snapshot.articles
            ],
        }


def _format_published_label(published: str) -> str:
    if not published:
        return ""
    return published.replace("T", " ").replace("Z", "")
