from __future__ import annotations

import asyncio
import copy

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import src.desktop.facades.github_workspace as github_workspace_module
from src.desktop.facades import GithubWorkspaceFacade


SUCCESS_NOTICE = "GitHub 趋势快照已刷新。"
DEGRADED_NOTICE_WITH_SNAPSHOT = "GitHub 抓取受限，已保留当前正式快照；恢复 GITHUB_TOKEN 后重试。"
DEGRADED_NOTICE_WITHOUT_SNAPSHOT = "GitHub 抓取受限，未生成正式快照；请配置 GITHUB_TOKEN 后重试。"
DEBOUNCE_WAIT_MS = github_workspace_module._FILTER_RELOAD_DEBOUNCE_MS + 30


def _snapshot(
    date: str,
    *,
    projects: list[dict],
    by_language: dict[str, int],
    by_category: dict[str, int],
) -> dict:
    return {
        "date": date,
        "generated_at": f"{date}T10:00:00+08:00",
        "stats": {
            "total": len(projects),
            "by_category": by_category,
            "by_language": by_language,
        },
        "projects": projects,
    }


def _fetch_result(snapshot: dict | None = None, *, outcome: str = "success", reason: str | None = None) -> dict:
    return {
        "outcome": outcome,
        "reason": reason,
        "snapshot": copy.deepcopy(snapshot),
        "partial_path": None if outcome == "success" else "D:/tmp/trending.partial.json",
    }


def _project(
    project_id: str,
    *,
    name: str,
    description: str,
    description_zh: str,
    language: str,
    category: str,
    stars: int,
    stars_today: int,
    stars_weekly: int,
    trend: str,
    updated_at: str,
) -> dict:
    return {
        "id": project_id,
        "full_name": name,
        "description": description,
        "description_zh": description_zh,
        "html_url": f"https://github.com/{name}",
        "homepage": None,
        "stars": stars,
        "forks": 10,
        "open_issues": 1,
        "language": language,
        "topics": [category],
        "category": category,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": updated_at,
        "pushed_at": updated_at,
        "owner_avatar": "",
        "owner_type": "Organization",
        "license": "MIT",
        "stars_today": stars_today,
        "stars_weekly": stars_weekly,
        "trend": trend,
    }


class FakeServices:
    def __init__(self) -> None:
        self.github_dates = ["2026-04-15", "2026-04-14"]
        self.snapshots = {
            "2026-04-15": _snapshot(
                "2026-04-15",
                projects=[
                    _project(
                        "acme/alpha",
                        name="acme/alpha",
                        description="Alpha helper",
                        description_zh="Alpha 助手",
                        language="Python",
                        category="llm",
                        stars=1200,
                        stars_today=25,
                        stars_weekly=180,
                        trend="rising",
                        updated_at="2026-04-15T08:00:00Z",
                    ),
                    _project(
                        "acme/beta",
                        name="acme/beta",
                        description="Beta helper",
                        description_zh="",
                        language="TypeScript",
                        category="agent",
                        stars=980,
                        stars_today=15,
                        stars_weekly=120,
                        trend="hot",
                        updated_at="2026-04-15T07:00:00Z",
                    ),
                ],
                by_language={"Python": 1, "TypeScript": 1},
                by_category={"llm": 1, "agent": 1},
            ),
            "2026-04-14": _snapshot(
                "2026-04-14",
                projects=[
                    _project(
                        "acme/gamma",
                        name="acme/gamma",
                        description="Gamma helper",
                        description_zh="Gamma 助手",
                        language="Python",
                        category="llm",
                        stars=760,
                        stars_today=8,
                        stars_weekly=60,
                        trend="stable",
                        updated_at="2026-04-14T08:00:00Z",
                    )
                ],
                by_language={"Python": 1},
                by_category={"llm": 1},
            ),
        }
        self.fetch_result = _fetch_result(self.snapshots["2026-04-15"])
        self.fetch_error: str | None = None
        self.date_calls = 0
        self.snapshot_calls: list[tuple[str, dict]] = []

    def get_github_dates(self) -> dict:
        self.date_calls += 1
        latest = self.github_dates[0] if self.github_dates else None
        return {"dates": list(self.github_dates), "latest": latest}

    def get_latest_github_trending(self, **kwargs) -> dict | None:
        latest = self.github_dates[0] if self.github_dates else None
        if latest is None:
            return None
        return self.get_github_trending_by_date(latest, **kwargs)

    def get_github_trending_by_date(self, date: str, **kwargs) -> dict | None:
        self.snapshot_calls.append((date, kwargs.copy()))
        snapshot = copy.deepcopy(self.snapshots.get(date))
        if snapshot is None:
            return None
        projects = list(snapshot["projects"])
        category = kwargs.get("category")
        language = kwargs.get("language", [])
        min_stars = kwargs.get("min_stars", 0)
        sort = kwargs.get("sort", "stars")
        query = kwargs.get("q")
        trend = kwargs.get("trend")
        if category:
            projects = [project for project in projects if project["category"] == category]
        if language:
            normalized = {item.casefold() for item in language}
            projects = [
                project
                for project in projects
                if str(project.get("language", "")).casefold() in normalized
            ]
        if min_stars > 0:
            projects = [project for project in projects if int(project.get("stars", 0) or 0) >= min_stars]
        if trend:
            projects = [project for project in projects if project.get("trend") == trend]
        if query:
            term = query.casefold()
            projects = [
                project
                for project in projects
                if term in project["full_name"].casefold()
                or term in str(project.get("description", "")).casefold()
                or term in str(project.get("description_zh", "")).casefold()
            ]
        if sort == "stars_today":
            projects.sort(key=lambda item: int(item.get("stars_today") or -1), reverse=True)
        elif sort == "stars_weekly":
            projects.sort(key=lambda item: int(item.get("stars_weekly") or -1), reverse=True)
        elif sort == "updated":
            projects.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
        else:
            projects.sort(key=lambda item: int(item.get("stars", 0) or 0), reverse=True)
        snapshot["projects"] = projects
        snapshot["stats"]["total"] = len(projects)
        return snapshot

    async def run_github_fetch_async(self, progress_callback=None) -> dict:
        if self.fetch_error:
            raise RuntimeError(self.fetch_error)
        if progress_callback is not None:
            progress_callback({"stage": "searching", "message": "Searching topic: llm"})
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
        except Exception as exc:  # pragma: no cover
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


def test_github_workspace_reload_selects_latest_snapshot(fake_services: FakeServices, qapp: QApplication) -> None:
    facade = GithubWorkspaceFacade(lambda: fake_services)

    facade.reload()
    qapp.processEvents()

    assert facade.currentDate == "2026-04-15"
    assert facade.snapshotModel.count == 2
    assert facade.projectModel.count == 2
    assert facade.selectedProjectName == "acme/alpha"
    assert facade.summaryText.startswith("2026-04-15")
    assert facade.statusTone == "neutral"
    assert facade.availableLanguages[0]["value"] == "Python"


def test_github_workspace_filter_changes_mark_stale_and_reload_clears_it(
    fake_services: FakeServices, qapp: QApplication
) -> None:
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()

    facade.setTrendFilter("rising")
    qapp.processEvents()

    assert facade.stale is True

    facade.reload()
    qapp.processEvents()

    assert facade.stale is False
    assert facade.projectModel.count == 1
    assert facade.selectedProjectName == "acme/alpha"


def test_github_workspace_supports_multi_language_filter(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()
    initial_calls = len(fake_services.snapshot_calls)

    facade.setSelectedLanguages(["Python", "TypeScript", "Python", ""])
    qapp.processEvents()

    assert facade.selectedLanguages == ["Python", "TypeScript"]
    assert facade.stale is True
    assert len(fake_services.snapshot_calls) == initial_calls

    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()

    assert facade.stale is False
    assert facade.projectModel.count == 2
    assert facade.selectedProjectName == "acme/alpha"
    assert len(fake_services.snapshot_calls) == initial_calls + 1
    assert fake_services.snapshot_calls[-1] == (
        "2026-04-15",
        {
            "category": None,
            "language": ["Python", "TypeScript"],
            "min_stars": 0,
            "sort": "stars",
            "q": None,
            "trend": None,
        },
    )


def test_github_workspace_filter_changes_debounce_to_latest_payload(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()
    initial_calls = len(fake_services.snapshot_calls)

    facade.setSearchQuery("alp")
    facade.setSearchQuery("alpha")
    facade.setMinStars(1000)
    facade.setSortKey("updated")
    facade.setTrendFilter("rising")
    qapp.processEvents()

    assert facade.stale is True
    assert len(fake_services.snapshot_calls) == initial_calls

    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()

    assert facade.stale is False
    assert facade.projectModel.count == 1
    assert facade.selectedProjectName == "acme/alpha"
    assert len(fake_services.snapshot_calls) == initial_calls + 1
    assert fake_services.snapshot_calls[-1] == (
        "2026-04-15",
        {
            "category": None,
            "language": [],
            "min_stars": 1000,
            "sort": "updated",
            "q": "alpha",
            "trend": "rising",
        },
    )


def test_github_workspace_clear_filters_uses_debounced_reload(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    facade.setSelectedLanguages(["Python"])
    facade.setSearchQuery("alpha")
    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()
    calls_after_filtered_reload = len(fake_services.snapshot_calls)

    assert facade.stale is False
    assert facade.projectModel.count == 1
    assert facade.selectedLanguages == ["Python"]
    assert facade.searchQuery == "alpha"

    facade.clearFilters()
    qapp.processEvents()

    assert facade.stale is True
    assert facade.selectedLanguages == []
    assert facade.searchQuery == ""
    assert len(fake_services.snapshot_calls) == calls_after_filtered_reload

    QTest.qWait(DEBOUNCE_WAIT_MS)
    qapp.processEvents()

    assert facade.stale is False
    assert facade.projectModel.count == 2
    assert facade.selectedProjectName == "acme/alpha"
    assert len(fake_services.snapshot_calls) == calls_after_filtered_reload


def test_github_workspace_snapshot_and_project_selection_refresh_detail(
    fake_services: FakeServices, qapp: QApplication
) -> None:
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()

    facade.selectDate("2026-04-14")
    qapp.processEvents()

    assert facade.currentDate == "2026-04-14"
    assert facade.projectModel.count == 1
    assert facade.selectedProjectName == "acme/gamma"

    facade.selectDate("2026-04-15")
    facade.selectProjectRow(1)
    qapp.processEvents()

    assert facade.selectedProjectName == "acme/beta"
    assert facade.selectedProjectUrl == "https://github.com/acme/beta"
    assert facade.selectedProjectDescription == "Beta helper"


def test_github_workspace_run_fetch_updates_busy_and_notice(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(github_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()

    facade.runFetch()
    qapp.processEvents()

    assert facade.busy is True
    assert facade.noticeMessage == "正在抓取 GitHub 趋势快照..."
    assert facade.fetchProgressValue == 5
    assert ControlledTaskThread.last_instance is not None

    ControlledTaskThread.last_instance.progress.emit(
        {"stage": "searching", "message": "Searching topic: llm", "current": 1, "total": 4}
    )
    qapp.processEvents()

    assert facade.fetchProgressValue == 26

    ControlledTaskThread.last_instance.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "success"
    assert facade.statusTone == "neutral"
    assert facade.noticeMessage == SUCCESS_NOTICE
    assert facade.fetchProgressValue == 100
    assert facade.currentDate == "2026-04-15"
    assert fake_services.date_calls == 2
    assert facade._task_thread is None
    assert facade._task_threads == {}


def test_github_workspace_run_fetch_degraded_keeps_current_snapshot(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_services.fetch_result = _fetch_result(outcome="degraded", reason="rate_limit")
    monkeypatch.setattr(github_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectDate("2026-04-14")

    facade.runFetch()
    ControlledTaskThread.last_instance.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "degraded"
    assert facade.statusTone == "warning"
    assert facade.fetchProgressValue == 100
    assert facade.errorMessage == ""
    assert facade.noticeMessage == DEGRADED_NOTICE_WITH_SNAPSHOT
    assert facade.currentDate == "2026-04-14"
    assert facade.projectModel.count == 1
    assert facade.selectedProjectName == "acme/gamma"
    assert facade._task_thread is None
    assert facade._task_threads == {}


def test_github_workspace_run_fetch_degraded_without_official_snapshot(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_services.github_dates = []
    fake_services.snapshots = {}
    fake_services.fetch_result = _fetch_result(outcome="degraded", reason="missing_token")
    monkeypatch.setattr(github_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    facade = GithubWorkspaceFacade(lambda: fake_services)

    facade.runFetch()
    ControlledTaskThread.last_instance.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "degraded"
    assert facade.statusTone == "warning"
    assert facade.fetchProgressValue == 100
    assert facade.noticeMessage == DEGRADED_NOTICE_WITHOUT_SNAPSHOT
    assert facade.currentDate == ""
    assert facade.projectModel.count == 0
    assert facade._task_thread is None
    assert facade._task_threads == {}


def test_github_workspace_run_fetch_failure_surfaces_error(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_services.fetch_error = "github failed"
    monkeypatch.setattr(github_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()

    facade.runFetch()
    qapp.processEvents()
    assert facade.busy is True

    ControlledTaskThread.last_instance.complete_failure()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.lastFetchOutcome == "error"
    assert facade.statusTone == "error"
    assert facade.fetchProgressValue == 100
    assert facade.errorMessage == "github failed"
    assert facade._task_thread is None
    assert facade._task_threads == {}


def test_github_workspace_discards_stale_fetch_result(
    fake_services: FakeServices,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(github_workspace_module, "AsyncTaskThread", ControlledTaskThread)
    ControlledTaskThread.instances.clear()
    facade = GithubWorkspaceFacade(lambda: fake_services)
    facade.reload()
    facade.selectDate("2026-04-14")
    qapp.processEvents()

    stale_snapshot = _snapshot(
        "2026-04-16",
        projects=[
            _project(
                "acme/stale",
                name="acme/stale",
                description="Stale helper",
                description_zh="旧助手",
                language="Python",
                category="llm",
                stars=100,
                stars_today=1,
                stars_weekly=2,
                trend="stable",
                updated_at="2026-04-16T08:00:00Z",
            )
        ],
        by_language={"Python": 1},
        by_category={"llm": 1},
    )
    latest_snapshot = _snapshot(
        "2026-04-17",
        projects=[
            _project(
                "acme/latest",
                name="acme/latest",
                description="Latest helper",
                description_zh="新助手",
                language="TypeScript",
                category="agent",
                stars=200,
                stars_today=5,
                stars_weekly=8,
                trend="rising",
                updated_at="2026-04-17T08:00:00Z",
            )
        ],
        by_language={"TypeScript": 1},
        by_category={"agent": 1},
    )

    fake_services.fetch_result = _fetch_result(stale_snapshot)
    facade.runFetch()
    first_task = ControlledTaskThread.instances[-1]
    qapp.processEvents()

    fake_services.github_dates = ["2026-04-17", "2026-04-15", "2026-04-14"]
    fake_services.snapshots["2026-04-17"] = latest_snapshot
    fake_services.fetch_result = _fetch_result(latest_snapshot)
    facade.runFetch()
    second_task = ControlledTaskThread.instances[-1]
    qapp.processEvents()

    assert first_task is not second_task
    assert facade.busy is True
    assert facade._task_thread is second_task
    assert len(facade._task_threads) == 2

    first_task.progress.emit({"stage": "searching", "message": "stale", "current": 4, "total": 4})
    qapp.processEvents()

    assert facade.noticeMessage == "正在抓取 GitHub 趋势快照..."

    second_task.complete_success()
    qapp.processEvents()

    assert facade.busy is False
    assert facade.currentDate == "2026-04-17"
    assert facade.selectedProjectName == "acme/latest"
    assert facade._task_thread is None
    assert len(facade._task_threads) == 1

    fake_services.github_dates = ["2026-04-16", "2026-04-17", "2026-04-15", "2026-04-14"]
    fake_services.snapshots["2026-04-16"] = stale_snapshot
    fake_services.fetch_result = _fetch_result(stale_snapshot)
    first_task.complete_success()
    qapp.processEvents()

    assert facade.currentDate == "2026-04-17"
    assert facade.selectedProjectName == "acme/latest"
    assert facade._task_threads == {}
