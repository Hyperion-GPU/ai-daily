from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Slot

from . import _SelectableListModel


class GithubSnapshotListModel(_SelectableListModel):
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
        super().__init__("date", "_selected_date", parent)

    @Slot(result=str)
    def selected_date(self) -> str:
        return self._selected_date

    @Slot(str, result=int)
    def row_for_date(self, date_value: str) -> int:
        return self._row_for_selection(date_value)

    def set_selected_date(self, date_value: str) -> None:
        self._select_value(date_value)

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
