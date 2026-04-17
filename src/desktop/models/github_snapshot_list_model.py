from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, Qt, Signal, Slot


class GithubSnapshotListModel(QAbstractListModel):
    countChanged = Signal()
    selectionChanged = Signal()

    _ROLE_NAMES = (
        "date",
        "label",
        "isSelected",
        "isLatest",
        "projectCount",
        "generatedAt",
    )
    _ROLE_IDS = {
        Qt.ItemDataRole.UserRole + index + 1: role_name
        for index, role_name in enumerate(_ROLE_NAMES)
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[dict[str, Any]] = []
        self._selected_date = ""

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
    def selected_date(self) -> str:
        return self._selected_date

    @Slot(str, result=int)
    def row_for_date(self, date_value: str) -> int:
        for index, item in enumerate(self._items):
            if item["date"] == date_value:
                return index
        return -1

    @Slot(result="QVariantMap")
    def selected_item(self) -> dict[str, Any]:
        row = self.row_for_date(self._selected_date)
        if row < 0:
            return {}
        return dict(self._items[row])

    def replace_items(self, items: list[dict[str, Any]]) -> None:
        previous_count = len(self._items)
        selected_date = self._selected_date
        if not selected_date:
            for item in items:
                if item.get("isSelected"):
                    selected_date = str(item.get("date", "") or "")
                    break

        normalized = [self._normalize_item(item, selected_date) for item in items]
        available_dates = {item["date"] for item in normalized}
        self.beginResetModel()
        self._items = normalized
        self._selected_date = selected_date if selected_date in available_dates else ""
        if self._selected_date:
            for item in self._items:
                item["isSelected"] = item["date"] == self._selected_date
        self.endResetModel()
        if previous_count != len(self._items):
            self.countChanged.emit()
        self.selectionChanged.emit()

    def clear(self) -> None:
        if not self._items and not self._selected_date:
            return
        previous_count = len(self._items)
        self.beginResetModel()
        self._items = []
        self._selected_date = ""
        self.endResetModel()
        if previous_count:
            self.countChanged.emit()
        self.selectionChanged.emit()

    def set_selected_date(self, date_value: str) -> None:
        date_value = str(date_value or "")
        if not date_value:
            previous_row = self.row_for_date(self._selected_date)
            if previous_row >= 0:
                self._selected_date = ""
                self._items[previous_row]["isSelected"] = False
                model_index = self.index(previous_row, 0)
                self.dataChanged.emit(model_index, model_index, list(self._ROLE_IDS.keys()))
                self.selectionChanged.emit()
            return

        new_row = self.row_for_date(date_value)
        if new_row < 0 or date_value == self._selected_date:
            return

        previous_row = self.row_for_date(self._selected_date)
        self._selected_date = date_value
        if previous_row >= 0:
            self._items[previous_row]["isSelected"] = False
            previous_index = self.index(previous_row, 0)
            self.dataChanged.emit(previous_index, previous_index, list(self._ROLE_IDS.keys()))

        self._items[new_row]["isSelected"] = True
        new_index = self.index(new_row, 0)
        self.dataChanged.emit(new_index, new_index, list(self._ROLE_IDS.keys()))
        self.selectionChanged.emit()

    def update_item_metadata(
        self,
        date_value: str,
        *,
        project_count: int | None,
        generated_at: str | None,
    ) -> None:
        row = self.row_for_date(date_value)
        if row < 0:
            return
        item = self._items[row]
        project_count = None if project_count is None else int(project_count)
        generated_at = generated_at or None
        if item["projectCount"] == project_count and item["generatedAt"] == generated_at:
            return
        item["projectCount"] = project_count
        item["generatedAt"] = generated_at
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, list(self._ROLE_IDS.keys()))

    @staticmethod
    def _normalize_item(item: dict[str, Any], selected_date: str) -> dict[str, Any]:
        date_value = str(item.get("date", "") or "")
        return {
            "date": date_value,
            "label": str(item.get("label", date_value) or date_value),
            "isSelected": date_value == selected_date,
            "isLatest": bool(item.get("isLatest", False)),
            "projectCount": item.get("projectCount"),
            "generatedAt": item.get("generatedAt"),
        }

    count = Property(int, get_count, notify=countChanged)
    selectedItem = Property("QVariantMap", selected_item, notify=selectionChanged)
