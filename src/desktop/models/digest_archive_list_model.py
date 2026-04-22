from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Slot

from . import _SelectableListModel


class DigestArchiveListModel(_SelectableListModel):
    _ROLE_NAMES = (
        "date",
        "label",
        "articleCount",
        "isLatest",
        "isSelected",
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

    @staticmethod
    def _normalize_item(item: dict[str, Any], selected_date: str) -> dict[str, Any]:
        date_value = str(item.get("date", "") or "")
        return {
            "date": date_value,
            "label": str(item.get("label", date_value) or date_value),
            "articleCount": int(item.get("articleCount", item.get("total", 0)) or 0),
            "isLatest": bool(item.get("isLatest", False)),
            "isSelected": date_value == selected_date,
        }
