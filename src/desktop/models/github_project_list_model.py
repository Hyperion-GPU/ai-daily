from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, Qt, Signal, Slot


class GithubProjectListModel(QAbstractListModel):
    countChanged = Signal()
    selectionChanged = Signal()

    _ROLE_NAMES = (
        "id",
        "fullName",
        "description",
        "descriptionZh",
        "htmlUrl",
        "language",
        "category",
        "stars",
        "starsToday",
        "starsWeekly",
        "trend",
        "updatedAt",
        "ownerAvatar",
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
    def row_for_id(self, project_id: str) -> int:
        for index, item in enumerate(self._items):
            if item["id"] == project_id:
                return index
        return -1

    @Slot(result="QVariantMap")
    def selected_item(self) -> dict[str, Any]:
        row = self.row_for_id(self._selected_id)
        if row < 0:
            return {}
        return dict(self._items[row])

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

    def set_selected_id(self, project_id: str) -> None:
        project_id = str(project_id or "")
        if not project_id:
            previous_row = self.row_for_id(self._selected_id)
            if previous_row >= 0:
                self._selected_id = ""
                self._items[previous_row]["isSelected"] = False
                model_index = self.index(previous_row, 0)
                self.dataChanged.emit(model_index, model_index, list(self._ROLE_IDS.keys()))
                self.selectionChanged.emit()
            return

        new_row = self.row_for_id(project_id)
        if new_row < 0 or project_id == self._selected_id:
            return

        previous_row = self.row_for_id(self._selected_id)
        self._selected_id = project_id
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
        project_id = str(item.get("id", "") or "")
        return {
            "id": project_id,
            "fullName": str(item.get("fullName", "") or ""),
            "description": str(item.get("description", "") or ""),
            "descriptionZh": str(item.get("descriptionZh", "") or ""),
            "htmlUrl": str(item.get("htmlUrl", "") or ""),
            "language": str(item.get("language", "") or ""),
            "category": str(item.get("category", "") or ""),
            "stars": int(item.get("stars", 0) or 0),
            "starsToday": item.get("starsToday"),
            "starsWeekly": item.get("starsWeekly"),
            "trend": str(item.get("trend", "") or ""),
            "updatedAt": str(item.get("updatedAt", "") or ""),
            "ownerAvatar": str(item.get("ownerAvatar", "") or ""),
            "topics": list(item.get("topics", []) or []),
            "forks": int(item.get("forks", 0) or 0),
            "license": str(item.get("license", "") or ""),
            "isSelected": project_id == selected_id,
        }

    count = Property(int, get_count, notify=countChanged)
    selectedItem = Property("QVariantMap", selected_item, notify=selectionChanged)
