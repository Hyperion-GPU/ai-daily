from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.desktop.models.digest_article_list_model import DigestArticleListModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def _articles() -> list[dict]:
    return [
        {
            "id": "paper-1",
            "title": "Reasoning with long context",
            "source_name": "arXiv",
            "source_category": "arxiv",
            "published": "2026-04-15T08:30:00Z",
            "summary_zh": "长上下文推理摘要",
            "importance": 5,
            "tags": ["reasoning", "llm"],
            "url": "https://example.com/paper-1",
        },
        {
            "id": "news-2",
            "title": "Model release notes",
            "sourceName": "OpenAI",
            "sourceCategory": "official",
            "sourceCategoryLabel": "官方来源",
            "published": "2026-04-15T09:00:00Z",
            "publishedLabel": "2026-04-15 09:00:00",
            "summaryZh": "版本更新摘要",
            "importance": 4,
            "tags": ["release"],
            "url": "https://example.com/news-2",
        },
    ]


def test_article_model_replace_and_select(qapp: QApplication) -> None:
    model = DigestArticleListModel()
    model.replace_items(_articles())

    assert model.count == 2
    assert model.row_for_id("paper-1") == 0
    assert model.selected_id() == ""

    model.set_selected_id("news-2")

    assert model.selected_id() == "news-2"
    assert model.selected_item()["title"] == "Model release notes"
    assert model.selectedItem["tags"] == ["release"]


def test_article_model_exposes_expected_roles(qapp: QApplication) -> None:
    model = DigestArticleListModel()
    model.replace_items(_articles())
    index = model.index(0, 0)
    roles = model.roleNames()

    assert model.data(index, next(role for role, name in roles.items() if name == b"sourceName")) == "arXiv"
    assert model.data(index, next(role for role, name in roles.items() if name == b"sourceCategoryLabel")) == "Arxiv"
    assert model.data(index, next(role for role, name in roles.items() if name == b"publishedLabel")) == "2026-04-15 08:30:00"
    assert model.data(index, next(role for role, name in roles.items() if name == b"summaryZh")) == "长上下文推理摘要"
    assert model.data(index, next(role for role, name in roles.items() if name == b"tags")) == ["reasoning", "llm"]
    assert model.data(index, next(role for role, name in roles.items() if name == b"isSelected")) is False


def test_article_model_clear_resets_selection(qapp: QApplication) -> None:
    model = DigestArticleListModel()
    model.replace_items(_articles())
    model.set_selected_id("paper-1")

    model.clear()

    assert model.count == 0
    assert model.selected_id() == ""
    assert model.selectedItem == {}


def test_article_model_emits_selection_and_count_signals(qapp: QApplication) -> None:
    model = DigestArticleListModel()
    count_events: list[None] = []
    selection_events: list[None] = []
    model.countChanged.connect(lambda: count_events.append(None))
    model.selectionChanged.connect(lambda: selection_events.append(None))

    model.replace_items(_articles())
    model.set_selected_id("paper-1")
    model.set_selected_id("paper-1")
    model.set_selected_id("missing")
    model.set_selected_id("")
    model.replace_items(_articles())
    model.clear()
    model.clear()

    assert len(count_events) == 2
    assert len(selection_events) == 5
