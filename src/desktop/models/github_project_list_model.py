from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Slot

from . import _SelectableListModel


class GithubProjectListModel(_SelectableListModel):
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
        super().__init__("id", "_selected_id", parent)

    @Slot(result=str)
    def selected_id(self) -> str:
        return self._selected_id

    @Slot(str, result=int)
    def row_for_id(self, project_id: str) -> int:
        return self._row_for_selection(project_id)

    def set_selected_id(self, project_id: str) -> None:
        self._select_value(project_id)

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
