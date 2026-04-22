from __future__ import annotations

import asyncio
import copy

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import src.desktop.facades.digest_workspace as digest_workspace_module
from src.desktop.facades.digest_workspace import DigestWorkspaceFacade


DEBOUNCE_WAIT_MS = digest_workspace_module._FILTER_RELOAD_DEBOUNCE_MS + 30


def _article(
    article_id: str,
    *,
    title: str,
    source_category: str,
    source_name: str,
    tags: list[str],
    importance: int,
    published: str,
) -> dict:
    return {
        "id": article_id,
        "title": title,
        "url": f"https://example.com/{article_id}",
        "published": published,
        "source_name": source_name,
        "source_category": source_category,
        "summary_zh": f"{title} summary",
        "tags": list(tags),
        "importance": importance,
    }


def _snapshot(date: str, articles: list[dict]) -> dict:
    by_category: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    for article in articles:
        category = str(article["source_category"])
        by_category[category] = by_category.get(category, 0) + 1
        for tag in article["tags"]:
            by_tag[tag] = by_tag.get(tag, 0) + 1
    return {
        "date": date,
        "generated_at": f"{date}T10:00:00+08:00",
        "stats": {
            "total": len(articles),
            "by_category": by_category,
            "by_tag": by_tag,
        },
        "articles": articles,
    }


class FakeServices:
    def __init__(self) -> None:
        self.dates = ["2026-04-15", "2026-04-14"]
        self.snapshots = {
            "2026-04-15": _snapshot(
                "2026-04-15",
                [
                    _article(
                        "alpha",
                        title="Alpha",
                        source_category="official",
                        source_name="Alpha Labs",
                        tags=["llm", "tools"],
                        importance=5,
                        published="2026-04-15T09:00:00+08:00",
                    ),
                    _article(
                        "beta",
                        title="Beta",
                        source_category="news",
                        source_name="Beta News",
                        tags=["agents"],
                        importance=3,
                        published="2026-04-15T08:00:00+08:00",
                    ),
                ],
            ),
            "2026-04-14": _snapshot(
                "2026-04-14",
                [
                    _article(
                        "gamma",
                        title="Gamma",
                        source_category="community",
                        source_name="Gamma Community",
                        tags=["llm"],
                        importance=4,
                        published="2026-04-14T09:00:00+08:00",
                    )
                ],
            ),
        }
        self.digest_calls: list[tuple[str, dict]] = []
        self.fetch_result: dict = {"result": "success", "article_count": 2}
        self.fetch_error: str | None = None
        self.fetch_snapshot: dict | None = None

    def get_dates(self) -> dict:
        return {
            "dates": [
                {
                    "date": date,
                    "total": self.snapshots[date]["stats"]["total"],
                    "by_category": self.snapshots[date]["stats"]["by_category"],
                }
                for date in self.dates
            ],
            "latest": self.dates[0] if self.dates else None,
        }

    def get_digest(self, date: str, **kwargs) -> dict | None:
        self.digest_calls.append((date, kwargs.copy()))
        raw = copy.deepcopy(self.snapshots.get(date))
        if raw is None:
            return None

        articles = list(raw["articles"])
        tags = list(kwargs.get("tags", []))
        category = kwargs.get("category")
        min_importance = int(kwargs.get("min_importance", 1) or 1)
        sort = kwargs.get("sort", "importance")
        query = kwargs.get("q")

        if tags:
            normalized = {str(tag).casefold() for tag in tags}
            articles = [
                article
                for article in articles
                if any(str(tag).casefold() in normalized for tag in article["tags"])
            ]
        if category:
            articles = [article for article in articles if article["source_category"] == category]
        if min_importance > 1:
            articles = [
                article for article in articles if int(article.get("importance", 0) or 0) >= min_importance
            ]
        if query:
            term = str(query).casefold()
            articles = [
                article
                for article in articles
                if term in article["title"].casefold()
                or term in str(article.get("summary_zh", "")).casefold()
            ]
        if sort == "published":
            articles.sort(key=lambda item: str(item.get("published", "")), reverse=True)
        else:
            articles.sort(key=lambda item: int(item.get("importance", 0) or 0), reverse=True)

        return _snapshot(date, articles)

    async def run_pipeline_async(self, progress_callback=None) -> dict:
        if self.fetch_error:
            raise RuntimeError(self.fetch_error)
        if progress_callback is not None:
            progress_callback({"stage": "stage1", "message": "Scored candidates", "current": 1, "total": 4})
        if self.fetch_snapshot is not None:
            date = str(self.fetch_snapshot["date"])
            self.snapshots[date] = copy.deepcopy(self.fetch_snapshot)
            self.dates = [date, *[item for item in self.dates if item != date]]
        return copy.deepcopy(self.fetch_result)


class ControlledTaskThread(QObject):
    progress = Signal(dict)
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()
    last_instance = None
    instances: list["ControlledTaskThread"] = []

    def __init__(self, runner, parent=None) -> None:
        super().__init__(parent)
        self._runner = runner
        ControlledTaskThread.last_instance = self
        ControlledTaskThread.instances.append(self)

    def start(self) -> None:
        return None

    def complete_success(self) -> None:
        result = asyncio.run(self._runner(self.progress.emit))
        self.succeeded.emit(result)
        self.finished.emit()

    def complete_failure(self) -> None:
        try:
            asyncio.run(self._runner(self.progress.emit))
        except Exception as exc:  # pragma: no cover - asserted through facade state
            self.failed.emit(
                {
                    "code": "runtime_error",
                    "stage": "task",
                    "message": str(exc),
                    "retryable": False,
                    "details": {"exceptionType": exc.__class__.__name__},
                }
            )
        self.finished.emit()


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


@pytest.fixture
def fake_services() -> FakeServices:
    return FakeServices()


def test_digest_workspace_reload_selects_latest_and_reuses_base_snapshot(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = DigestWorkspaceFacade(lambda: fake_services)

    facade.reload()
    qapp.processEvents()

    assert facade.currentDate == "2026-04-15"
    assert facade.archiveModel.count == 2
    assert facade.archiveCount == 2
    assert facade.currentDateArticleCount == 2
    assert facade.filteredArticleCount == 2
    assert facade.selectedArticleId == "alpha"
    assert facade.selectedArticle["title"] == "Alpha"
    assert [item["value"] for item in facade.availableTags] == ["agents", "llm", "tools"]
    assert fake_services.digest_calls == [
        (
            "2026-04-15",
            {
                "tags": [],
                "category": None,
                "min_importance": 1,
                "sort": "importance",
                "q": None,
            },
        )
    ]


def test_digest_workspace_filter_changes_are_debounced_and_reuse_base_snapshot(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectArticleRow(0)
    qapp.processEvents()

    facade.markStale()
    qapp.processEvents()
    assert facade.stale is True

    initial_calls = len(fake_services.digest_calls)
    facade.setCategoryFilter("news")
    qapp.processEvents()

    assert len(fake_services.digest_calls) == initial_calls

    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()

    assert len(fake_services.digest_calls) == initial_calls + 1
    assert facade.stale is False
    assert facade.currentDateArticleCount == 2
    assert facade.filteredArticleCount == 1
    assert facade.selectedArticleId == "beta"
    assert [item["value"] for item in facade.availableTags] == ["agents", "llm", "tools"]
    assert fake_services.digest_calls[-1] == (
        "2026-04-15",
        {
            "tags": [],
            "category": "news",
            "min_importance": 1,
            "sort": "importance",
            "q": None,
        },
    )


def test_digest_workspace_debounce_keeps_latest_filter_only(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    initial_calls = len(fake_services.digest_calls)
    facade.setSearchQuery("a")
    facade.setSearchQuery("al")
    facade.setSearchQuery("alpha")
    facade.setMinImportance(5)
    qapp.processEvents()

    assert len(fake_services.digest_calls) == initial_calls

    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()

    assert len(fake_services.digest_calls) == initial_calls + 1
    assert facade.filteredArticleCount == 1
    assert facade.selectedArticleId == "alpha"
    assert "搜索 “alpha”" in facade.summaryText
    assert fake_services.digest_calls[-1] == (
        "2026-04-15",
        {
            "tags": [],
            "category": None,
            "min_importance": 5,
            "sort": "importance",
            "q": "alpha",
        },
    )


def test_digest_workspace_pending_filter_reload_does_not_outlive_newer_date_selection(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    facade.setSearchQuery("gamma")
    qapp.processEvents()
    assert len(fake_services.digest_calls) == 1

    facade.selectDate("2026-04-14")
    qapp.processEvents()
    calls_after_select = len(fake_services.digest_calls)

    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()

    assert len(fake_services.digest_calls) == calls_after_select
    assert facade.currentDate == "2026-04-14"
    assert facade.selectedArticleId == "gamma"
    assert fake_services.digest_calls[-2:] == [
        (
            "2026-04-14",
            {
                "tags": [],
                "category": None,
                "min_importance": 1,
                "sort": "importance",
                "q": None,
            },
        ),
        (
            "2026-04-14",
            {
                "tags": [],
                "category": None,
                "min_importance": 1,
                "sort": "importance",
                "q": "gamma",
            },
        ),
    ]


def test_digest_workspace_run_fetch_success_selects_latest_archive_and_open_action(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened_urls: list[str] = []
    fake_services.fetch_snapshot = _snapshot(
        "2026-04-16",
        [
            _article(
                "delta",
                title="Delta",
                source_category="official",
                source_name="Delta Labs",
                tags=["llm"],
                importance=5,
                published="2026-04-16T09:00:00+08:00",
            )
        ],
    )
    monkeypatch.setattr(digest_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    monkeypatch.setattr(
        digest_workspace_module.QDesktopServices,
        "openUrl",
        lambda url: opened_urls.append(url.toString()) or True,
    )
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectDate("2026-04-14")
    qapp.processEvents()

    facade.runFetch()
    qapp.processEvents()

    assert facade.busy is True
    assert facade.noticeMessage == "正在抓取 RSS 与摘要..."
    assert facade.pipelineProgressValue == 5
    assert ControlledTaskThread.last_instance is not None

    ControlledTaskThread.last_instance.progress.emit(
        {"stage": "stage2", "message": "Drafted summaries", "current": 3, "total": 4}
    )
    qapp.processEvents()

    assert facade.pipelineProgressText == "stage2: Drafted summaries"
    assert facade.pipelineProgressValue == 75
    assert facade.noticeMessage == "stage2: Drafted summaries"

    ControlledTaskThread.last_instance.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "success"
    assert facade.currentDate == "2026-04-16"
    assert facade.archiveCount == 3
    assert facade.selectedArticleId == "delta"
    assert facade.selectedArticle["title"] == "Delta"
    assert facade.noticeMessage == "今日日报已更新。"
    assert facade.pipelineProgressText == "completed: 已完成"
    assert facade.pipelineProgressValue == 100
    assert facade._task_thread is None
    assert facade._task_threads == {}

    facade.openSelectedArticle()

    assert opened_urls == ["https://example.com/delta"]


def test_digest_workspace_run_fetch_no_new_items_keeps_current_context(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_services.fetch_result = {"result": "no_new_items", "article_count": 1}
    monkeypatch.setattr(digest_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectDate("2026-04-14")
    qapp.processEvents()

    assert facade.currentDate == "2026-04-14"
    assert facade.selectedArticleId == "gamma"

    facade.runFetch()
    qapp.processEvents()
    ControlledTaskThread.last_instance.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "no_new_items"
    assert facade.currentDate == "2026-04-14"
    assert facade.selectedArticleId == "gamma"
    assert facade.noticeMessage == "没有新的日报内容，已保留现有归档。"
    assert facade._task_thread is None
    assert facade._task_threads == {}


def test_digest_workspace_run_fetch_failure_surfaces_error(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_services.fetch_error = "digest failed"
    monkeypatch.setattr(digest_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectDate("2026-04-14")
    qapp.processEvents()

    facade.runFetch()
    qapp.processEvents()
    assert facade.busy is True

    ControlledTaskThread.last_instance.complete_failure()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "error"
    assert facade.currentDate == "2026-04-14"
    assert facade.selectedArticleId == "gamma"
    assert facade.errorMessage == "digest failed"
    assert facade.pipelineProgressText == "error: digest failed"
    assert facade._task_thread is None
    assert facade._task_threads == {}


def test_digest_workspace_discards_stale_fetch_result(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(digest_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    ControlledTaskThread.instances.clear()
    facade = DigestWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectDate("2026-04-14")
    qapp.processEvents()

    stale_snapshot = _snapshot(
        "2026-04-16",
        [
            _article(
                "stale",
                title="Stale",
                source_category="official",
                source_name="Stale Labs",
                tags=["old"],
                importance=5,
                published="2026-04-16T09:00:00+08:00",
            )
        ],
    )
    latest_snapshot = _snapshot(
        "2026-04-17",
        [
            _article(
                "latest",
                title="Latest",
                source_category="official",
                source_name="Latest Labs",
                tags=["new"],
                importance=5,
                published="2026-04-17T09:00:00+08:00",
            )
        ],
    )

    fake_services.fetch_snapshot = stale_snapshot
    facade.runFetch()
    first_task = ControlledTaskThread.instances[-1]
    qapp.processEvents()

    fake_services.fetch_snapshot = latest_snapshot
    facade.runFetch()
    second_task = ControlledTaskThread.instances[-1]
    qapp.processEvents()

    assert first_task is not second_task
    assert facade.busy is True
    assert facade._task_thread is second_task
    assert len(facade._task_threads) == 2

    first_task.progress.emit({"stage": "stage2", "message": "stale progress", "current": 4, "total": 4})
    qapp.processEvents()

    assert facade.pipelineProgressText == "starting: 正在抓取 RSS 与摘要..."

    second_task.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.currentDate == "2026-04-17"
    assert facade.selectedArticleId == "latest"
    assert facade._task_thread is None
    assert len(facade._task_threads) == 1

    fake_services.fetch_snapshot = stale_snapshot
    first_task.complete_success()
    qapp.processEvents()

    assert facade.currentDate == "2026-04-17"
    assert facade.selectedArticleId == "latest"
    assert facade._task_threads == {}
