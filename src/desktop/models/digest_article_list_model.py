from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Slot

from ._selectable_list_model import _SelectableListModel


_SOURCE_CATEGORY_LABELS = {
    "arxiv": "Arxiv",
    "official": "官方",
    "news": "新闻",
    "community": "社区",
}


class DigestArticleListModel(_SelectableListModel):
    _ROLE_NAMES = (
        "id",
        "title",
        "sourceName",
        "sourceCategory",
        "sourceCategoryLabel",
        "published",
        "publishedLabel",
        "summaryZh",
        "importance",
        "tags",
        "url",
        "isSelected",
    )
    _ROLE_IDS = {
        Qt.ItemDataRole.UserRole + index + 1: role_name
        for index, role_name in enumerate(_ROLE_NAMES)
    }

    def __init__(self, parent=None) -> None:
        super().__init__("id", "_selected_id", parent)

    @Slot(result=str)
    def selected_id(self) -> str:
        return self._selected_id

    @Slot(str, result=int)
    def row_for_id(self, article_id: str) -> int:
        return self._row_for_selection(article_id)

    def set_selected_id(self, article_id: str) -> None:
        self._select_value(article_id)

    def _copy_selected_item(self, item: dict[str, Any]) -> dict[str, Any]:
        copied = dict(item)
        copied["tags"] = list(copied.get("tags", []))
        return copied

    @staticmethod
    def _normalize_item(item: dict[str, Any], selected_id: str) -> dict[str, Any]:
        article_id = str(item.get("id", "") or "")
        source_category = str(item.get("sourceCategory", item.get("source_category", "")) or "")
        source_category_label = str(
            item.get("sourceCategoryLabel")
            or _SOURCE_CATEGORY_LABELS.get(source_category)
            or source_category
            or "未分类"
        )
        published = str(item.get("published", "") or "")
        tags = [str(tag) for tag in list(item.get("tags", []) or []) if str(tag)]
        return {
            "id": article_id,
            "title": str(item.get("title", "") or ""),
            "sourceName": str(item.get("sourceName", item.get("source_name", "")) or ""),
            "sourceCategory": source_category,
            "sourceCategoryLabel": source_category_label,
            "published": published,
            "publishedLabel": str(item.get("publishedLabel") or _format_published_label(published)),
            "summaryZh": str(item.get("summaryZh", item.get("summary_zh", "")) or ""),
            "importance": int(item.get("importance", 0) or 0),
            "tags": tags,
            "url": str(item.get("url", "") or ""),
            "isSelected": article_id == selected_id,
        }

def _format_published_label(published: str) -> str:
    if not published:
        return ""
    return published.replace("T", " ").replace("Z", "")
