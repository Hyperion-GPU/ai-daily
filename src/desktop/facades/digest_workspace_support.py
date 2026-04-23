from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from ..tasks import DigestCommandGateway


@dataclass(slots=True)
class DigestFilterState:
    category_filter: str = ""
    selected_tags: list[str] = field(default_factory=list)
    min_importance: int = 1
    sort_key: str = "importance"
    search_query: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "selectedTags": list(self.selected_tags),
            "categoryFilter": self.category_filter,
            "minImportance": self.min_importance,
            "sortKey": self.sort_key,
            "searchQuery": self.search_query,
        }

    @staticmethod
    def base_payload() -> dict[str, Any]:
        return {
            "selectedTags": [],
            "categoryFilter": "",
            "minImportance": 1,
            "sortKey": "importance",
            "searchQuery": "",
        }

    def is_base(self) -> bool:
        return self.payload() == self.base_payload()

    def sync_selected_tags_to_available(self, available_tags: list[dict[str, Any]]) -> bool:
        if not self.selected_tags:
            return False
        visible = {item["value"] for item in available_tags}
        filtered = [tag for tag in self.selected_tags if tag in visible]
        if filtered == self.selected_tags:
            return False
        self.selected_tags = filtered
        return True

    def summary_text(self, *, current_date: str, filtered_count: int, sort_labels: dict[str, str]) -> str:
        if not current_date:
            return ""
        parts = [
            current_date,
            f"{filtered_count} 篇文章",
            sort_labels.get(self.sort_key, self.sort_key),
        ]
        if self.search_query:
            parts.append(f'搜索 “{self.search_query}”')
        if self.category_filter:
            parts.append(f"分类 {self.category_filter}")
        if self.selected_tags:
            parts.append("标签 " + " / ".join(self.selected_tags))
        return " · ".join(parts)


@dataclass(frozen=True, slots=True)
class DigestSnapshotLoad:
    base_snapshot: dict[str, Any] | None
    filtered_snapshot: dict[str, Any] | None
    current_article_count: int
    available_tags: list[dict[str, Any]]


class DigestSnapshotLoader:
    def __init__(self, gateway: DigestCommandGateway) -> None:
        self._gateway = gateway
        self._base_snapshot_cache: dict[str, dict[str, Any] | None] = {}
        self._cache_lock = RLock()
        self._cache_revision = 0

    def invalidate_cache(self) -> None:
        with self._cache_lock:
            self._base_snapshot_cache.clear()
            self._cache_revision += 1

    def prune_cache(self, available_dates: set[str]) -> None:
        with self._cache_lock:
            for cached_date in list(self._base_snapshot_cache):
                if cached_date not in available_dates:
                    self._base_snapshot_cache.pop(cached_date, None)
            self._cache_revision += 1

    def load(self, date_value: str, filters: DigestFilterState) -> DigestSnapshotLoad:
        base_snapshot = self._load_base_snapshot(date_value)
        if filters.is_base():
            filtered_snapshot = base_snapshot
        else:
            filtered_snapshot = self._gateway.load_snapshot(date_value, filters.payload())
        return DigestSnapshotLoad(
            base_snapshot=base_snapshot,
            filtered_snapshot=filtered_snapshot,
            current_article_count=int((base_snapshot or {}).get("stats", {}).get("total", 0) or 0),
            available_tags=available_tags_from_snapshot(base_snapshot),
        )

    def _load_base_snapshot(self, date_value: str) -> dict[str, Any] | None:
        with self._cache_lock:
            if date_value in self._base_snapshot_cache:
                return self._base_snapshot_cache[date_value]
            revision = self._cache_revision
        snapshot = self._gateway.load_snapshot(
            date_value,
            DigestFilterState.base_payload(),
        )
        with self._cache_lock:
            if revision == self._cache_revision:
                self._base_snapshot_cache[date_value] = snapshot
                return self._base_snapshot_cache[date_value]
        return snapshot


def available_tags_from_snapshot(snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    by_tag = dict((snapshot or {}).get("stats", {}).get("byTag", {}) or {})
    return [
        {
            "value": str(tag),
            "label": f"{tag} ({count})",
            "count": int(count),
        }
        for tag, count in sorted(
            by_tag.items(),
            key=lambda item: (-int(item[1]), str(item[0]).casefold()),
        )
        if str(tag).strip()
    ]
