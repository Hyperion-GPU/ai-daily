from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.desktop.models import GithubProjectListModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def _projects() -> list[dict]:
    return [
        {
            "id": "acme/alpha",
            "fullName": "acme/alpha",
            "description": "Alpha helper",
            "descriptionZh": "Alpha 助手",
            "htmlUrl": "https://github.com/acme/alpha",
            "language": "Python",
            "category": "llm",
            "stars": 1200,
            "starsToday": 25,
            "starsWeekly": 180,
            "trend": "rising",
            "updatedAt": "2026-04-15T08:00:00Z",
            "ownerAvatar": "",
        },
        {
            "id": "acme/beta",
            "fullName": "acme/beta",
            "description": "Beta helper",
            "descriptionZh": "",
            "htmlUrl": "https://github.com/acme/beta",
            "language": "TypeScript",
            "category": "agent",
            "stars": 980,
            "starsToday": 15,
            "starsWeekly": 120,
            "trend": "hot",
            "updatedAt": "2026-04-15T07:00:00Z",
            "ownerAvatar": "",
        },
    ]


def test_project_model_replace_and_select(qapp: QApplication) -> None:
    model = GithubProjectListModel()
    model.replace_items(_projects())

    assert model.count == 2
    assert model.row_for_id("acme/alpha") == 0
    assert model.selected_id() == ""

    model.set_selected_id("acme/beta")

    assert model.selected_id() == "acme/beta"
    assert model.selected_item()["fullName"] == "acme/beta"
    assert model.selectedItem["fullName"] == "acme/beta"


def test_project_model_exposes_expected_roles(qapp: QApplication) -> None:
    model = GithubProjectListModel()
    model.replace_items(_projects())
    index = model.index(0, 0)
    roles = model.roleNames()

    assert model.data(index, next(role for role, name in roles.items() if name == b"fullName")) == "acme/alpha"
    assert model.data(index, next(role for role, name in roles.items() if name == b"starsToday")) == 25
    assert model.data(index, next(role for role, name in roles.items() if name == b"isSelected")) is False


def test_project_model_clear_resets_selection(qapp: QApplication) -> None:
    model = GithubProjectListModel()
    model.replace_items(_projects())
    model.set_selected_id("acme/alpha")

    model.clear()

    assert model.count == 0
    assert model.selected_id() == ""
    assert model.selected_item() == {}
