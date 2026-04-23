from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, Qt, Signal, Slot


class _SelectableListModel(QAbstractListModel):
    countChanged = Signal()
    selectionChanged = Signal()

    _ROLE_IDS: dict[int, str] = {}

    def __init__(self, selection_key: str, selection_attr: str, parent=None) -> None:
        super().__init__(parent)
        self._items: list[dict[str, Any]] = []
        self._selection_key = selection_key
        self._selection_attr = selection_attr
        setattr(self, selection_attr, "")

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

    @Slot(result="QVariantMap")
    def selected_item(self) -> dict[str, Any]:
        row = self._row_for_selection(self._selected_value())
        if row < 0:
            return {}
        return self._copy_selected_item(self._items[row])

    def replace_items(self, items: list[dict[str, Any]]) -> None:
        previous_count = len(self._items)
        selected_value = self._selected_value()
        if not selected_value:
            selected_value = self._selected_value_from_items(items)

        normalized = [self._normalize_item(item, selected_value) for item in items]
        available_values = {item[self._selection_key] for item in normalized}
        self.beginResetModel()
        self._items = normalized
        selected_value = selected_value if selected_value in available_values else ""
        self._set_selected_value(selected_value)
        if selected_value:
            for item in self._items:
                item["isSelected"] = item[self._selection_key] == selected_value
        self.endResetModel()
        if previous_count != len(self._items):
            self.countChanged.emit()
        self.selectionChanged.emit()

    def clear(self) -> None:
        if not self._items and not self._selected_value():
            return
        previous_count = len(self._items)
        self.beginResetModel()
        self._items = []
        self._set_selected_value("")
        self.endResetModel()
        if previous_count:
            self.countChanged.emit()
        self.selectionChanged.emit()

    def _set_selected_value(self, selected_value: str) -> None:
        setattr(self, self._selection_attr, str(selected_value or ""))

    def _selected_value(self) -> str:
        return str(getattr(self, self._selection_attr))

    def _selected_value_from_items(self, items: list[dict[str, Any]]) -> str:
        for item in items:
            if item.get("isSelected"):
                return str(item.get(self._selection_key, "") or "")
        return ""

    def _row_for_selection(self, selected_value: str) -> int:
        for index, item in enumerate(self._items):
            if item[self._selection_key] == selected_value:
                return index
        return -1

    def _select_value(self, selected_value: str) -> None:
        selected_value = str(selected_value or "")
        if not selected_value:
            previous_row = self._row_for_selection(self._selected_value())
            if previous_row >= 0:
                self._set_selected_value("")
                self._items[previous_row]["isSelected"] = False
                self._emit_row_changed(previous_row)
                self.selectionChanged.emit()
            return

        new_row = self._row_for_selection(selected_value)
        if new_row < 0 or selected_value == self._selected_value():
            return

        previous_row = self._row_for_selection(self._selected_value())
        self._set_selected_value(selected_value)
        if previous_row >= 0:
            self._items[previous_row]["isSelected"] = False
            self._emit_row_changed(previous_row)

        self._items[new_row]["isSelected"] = True
        self._emit_row_changed(new_row)
        self.selectionChanged.emit()

    def _emit_row_changed(self, row: int) -> None:
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, list(self._ROLE_IDS.keys()))

    def _copy_selected_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return dict(item)

    def _normalize_item(self, item: dict[str, Any], selected_value: str) -> dict[str, Any]:
        raise NotImplementedError

    count = Property(int, get_count, notify=countChanged)
    selectedItem = Property("QVariantMap", selected_item, notify=selectionChanged)
