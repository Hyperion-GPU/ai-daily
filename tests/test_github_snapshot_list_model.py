from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.desktop.models import GithubSnapshotListModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def test_snapshot_model_replace_and_select(qapp: QApplication) -> None:
    model = GithubSnapshotListModel()
    model.replace_items(
        [
            {"date": "2026-04-15", "label": "2026-04-15", "isLatest": True},
            {"date": "2026-04-14", "label": "2026-04-14", "isLatest": False},
        ]
    )

    assert model.count == 2
    assert model.row_for_date("2026-04-15") == 0
    assert model.selected_date() == ""

    model.set_selected_date("2026-04-14")

    assert model.selected_date() == "2026-04-14"
    assert model.selectedItem["date"] == "2026-04-14"


def test_snapshot_model_updates_delayed_metadata(qapp: QApplication) -> None:
    model = GithubSnapshotListModel()
    model.replace_items([{"date": "2026-04-15", "label": "2026-04-15", "isLatest": True}])

    model.update_item_metadata(
        "2026-04-15",
        project_count=12,
        generated_at="2026-04-15T10:00:00+08:00",
    )

    item = model.index(0, 0)
    roles = model.roleNames()
    assert model.data(item, next(role for role, name in roles.items() if name == b"projectCount")) == 12
    assert (
        model.data(item, next(role for role, name in roles.items() if name == b"generatedAt"))
        == "2026-04-15T10:00:00+08:00"
    )


def test_snapshot_model_clear_resets_selection(qapp: QApplication) -> None:
    model = GithubSnapshotListModel()
    model.replace_items([{"date": "2026-04-15", "label": "2026-04-15", "isLatest": True}])
    model.set_selected_date("2026-04-15")

    model.clear()

    assert model.count == 0
    assert model.selected_date() == ""
    assert model.selectedItem == {}
