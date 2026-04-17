from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.desktop.models.digest_archive_list_model import DigestArchiveListModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def _archives() -> list[dict]:
    return [
        {
            "date": "2026-04-15",
            "label": "2026-04-15",
            "total": 12,
            "isLatest": True,
        },
        {
            "date": "2026-04-14",
            "articleCount": 7,
            "isLatest": False,
        },
    ]


def test_archive_model_replace_and_select(qapp: QApplication) -> None:
    model = DigestArchiveListModel()
    model.replace_items(_archives())

    assert model.count == 2
    assert model.row_for_date("2026-04-15") == 0
    assert model.selected_date() == ""

    model.set_selected_date("2026-04-14")

    assert model.selected_date() == "2026-04-14"
    assert model.selected_item()["date"] == "2026-04-14"
    assert model.selectedItem["articleCount"] == 7


def test_archive_model_exposes_expected_roles(qapp: QApplication) -> None:
    model = DigestArchiveListModel()
    model.replace_items(_archives())
    index = model.index(0, 0)
    roles = model.roleNames()

    assert model.data(index, next(role for role, name in roles.items() if name == b"label")) == "2026-04-15"
    assert model.data(index, next(role for role, name in roles.items() if name == b"articleCount")) == 12
    assert model.data(index, next(role for role, name in roles.items() if name == b"isLatest")) is True
    assert model.data(index, next(role for role, name in roles.items() if name == b"isSelected")) is False


def test_archive_model_clear_resets_selection(qapp: QApplication) -> None:
    model = DigestArchiveListModel()
    model.replace_items(_archives())
    model.set_selected_date("2026-04-15")

    model.clear()

    assert model.count == 0
    assert model.selected_date() == ""
    assert model.selectedItem == {}
