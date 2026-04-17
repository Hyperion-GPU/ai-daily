from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, Qt, Signal, Slot


_SOURCE_CATEGORY_LABELS = {
    "arxiv": "Arxiv",
    "official": "官方",
    "news": "新闻",
    "community": "社区",
}


class DigestArticleListModel(QAbstractListModel):
    countChanged = Signal()
    selectionChanged = Signal()

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
        super().__init__(parent)
        self._items: list[dict[str, Any]] = []
        self._selected_id = ""

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    def roleNames(self) -> dict[int, bytes]:
        return {
            role_id: role_name.encode("utf-8")
            for role_id, role_name in self._ROLE_IDS.items()
        }

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        role_name = self._ROLE_IDS.get(role)
        if role_name is None:
            return None
        return self._items[row].get(role_name)

    def get_count(self) -> int:
        return len(self._items)

    @Slot(result=str)
    def selected_id(self) -> str:
        return self._selected_id

    @Slot(str, result=int)
    def row_for_id(self, article_id: str) -> int:
        for index, item in enumerate(self._items):
            if item["id"] == article_id:
                return index
        return -1

    @Slot(result="QVariantMap")
    def selected_item(self) -> dict[str, Any]:
        row = self.row_for_id(self._selected_id)
        if row < 0:
            return {}
        item = dict(self._items[row])
        item["tags"] = list(item.get("tags", []))
        return item

    def replace_items(self, items: list[dict[str, Any]]) -> None:
        previous_count = len(self._items)
        selected_id = self._selected_id
        if not selected_id:
            for item in items:
                if item.get("isSelected"):
                    selected_id = str(item.get("id", "") or "")
                    break

        normalized = [self._normalize_item(item, selected_id) for item in items]
        available_ids = {item["id"] for item in normalized}
        self.beginResetModel()
        self._items = normalized
        self._selected_id = selected_id if selected_id in available_ids else ""
        if self._selected_id:
            for item in self._items:
                item["isSelected"] = item["id"] == self._selected_id
        self.endResetModel()
        if previous_count != len(self._items):
            self.countChanged.emit()
        self.selectionChanged.emit()

    def clear(self) -> None:
        if not self._items and not self._selected_id:
            return
        previous_count = len(self._items)
        self.beginResetModel()
        self._items = []
        self._selected_id = ""
        self.endResetModel()
        if previous_count:
            self.countChanged.emit()
        self.selectionChanged.emit()

    def set_selected_id(self, article_id: str) -> None:
        article_id = str(article_id or "")
        if not article_id:
            previous_row = self.row_for_id(self._selected_id)
            if previous_row >= 0:
                self._selected_id = ""
                self._items[previous_row]["isSelected"] = False
                model_index = self.index(previous_row, 0)
                self.dataChanged.emit(model_index, model_index, list(self._ROLE_IDS.keys()))
                self.selectionChanged.emit()
            return

        new_row = self.row_for_id(article_id)
        if new_row < 0 or article_id == self._selected_id:
            return

        previous_row = self.row_for_id(self._selected_id)
        self._selected_id = article_id
        if previous_row >= 0:
            self._items[previous_row]["isSelected"] = False
            previous_index = self.index(previous_row, 0)
            self.dataChanged.emit(previous_index, previous_index, list(self._ROLE_IDS.keys()))

        self._items[new_row]["isSelected"] = True
        new_index = self.index(new_row, 0)
        self.dataChanged.emit(new_index, new_index, list(self._ROLE_IDS.keys()))
        self.selectionChanged.emit()

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

    count = Property(int, get_count, notify=countChanged)
    selectedItem = Property("QVariantMap", selected_item, notify=selectionChanged)


def _format_published_label(published: str) -> str:
    if not published:
        return ""
    return published.replace("T", " ").replace("Z", "")
