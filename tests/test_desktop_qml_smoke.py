from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("AI_DAILY_QML_STYLE", "Basic")

import copy
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QFile, QIODevice, QObject
from PySide6.QtQuickControls2 import QQuickStyle

from src.desktop.qml_app import DEFAULT_QUICK_STYLE, QML_MAIN_URL, RESOURCE_BUNDLE_PATH, create_qml_runtime

REPO_ROOT = Path(__file__).resolve().parents[1]
QRC_PATH = REPO_ROOT / "src" / "desktop" / "resources.qrc"


class FakeConfigurationService:
    def __init__(self) -> None:
        self._persisted_config: dict = {}
        self.llm_api_key = "sk-test"
        self.github_token = ""

    def load(self, *, mode: str = "desktop") -> dict:
        _ = mode
        return copy.deepcopy(self._persisted_config)

    def save(self, config: dict, *, mode: str = "desktop"):
        _ = mode
        self._persisted_config = copy.deepcopy(config)
        return None

    def get_llm_api_key(self, config: dict) -> str | None:
        _ = config
        return self.llm_api_key

    def set_llm_api_key(self, config: dict, value: str | None) -> None:
        _ = config
        self.llm_api_key = (value or "").strip()

    def get_github_token(self, config: dict) -> str | None:
        _ = config
        return self.github_token

    def set_github_token(self, value: str | None) -> None:
        self.github_token = (value or "").strip()

    def user_data_dir(self):
        return REPO_ROOT


class FakeServices:
    def __init__(self) -> None:
        self._config = {
            "timezone": "Asia/Shanghai",
            "llm": {
                "provider": "siliconflow",
                "siliconflow": {
                    "base_url": "https://api.siliconflow.cn/v1",
                    "model": "deepseek-ai/DeepSeek-V3.2",
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
                "newapi": {
                    "base_url": "https://example.com/newapi",
                    "model": "deepseek-chat",
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
            },
            "pipeline": {
                "time_window_hours": 48,
                "max_articles_per_day": 30,
                "max_articles_to_stage2": 50,
                "stage1_batch_size": 50,
            },
            "github_trending": {
                "enabled": False,
                "min_stars": 500,
                "max_projects_per_day": 50,
            },
        }
        self.configuration_service = FakeConfigurationService()
        self.configuration_service._persisted_config = copy.deepcopy(self._config)

    def current_config(self) -> dict:
        return copy.deepcopy(self._config)

    def replace_config(self, config: dict) -> None:
        self._config = copy.deepcopy(config)

    def get_github_dates(self) -> dict:
        return {"dates": ["2026-04-15"], "latest": "2026-04-15"}

    def get_dates(self) -> dict:
        return {
            "dates": [
                {
                    "date": "2026-04-15",
                    "total": 2,
                    "by_category": {"news": 1, "official": 1},
                }
            ],
            "latest": "2026-04-15",
        }

    def get_digest(
        self,
        date: str,
        *,
        tags: list[str],
        category: str | None,
        min_importance: int,
        sort: str,
        q: str | None,
    ) -> dict | None:
        articles = [
            {
                "id": "digest-1",
                "title": "OpenAI updates desktop workflow",
                "url": "https://example.com/openai",
                "published": "2026-04-15T08:30:00Z",
                "source_name": "OpenAI",
                "source_category": "official",
                "summary_zh": "官方更新强调桌面工作流与资源同步。",
                "tags": ["OpenAI", "Desktop"],
                "importance": 5,
            },
            {
                "id": "digest-2",
                "title": "Agent tooling roundup",
                "url": "https://example.com/agent",
                "published": "2026-04-15T07:00:00Z",
                "source_name": "AI Daily",
                "source_category": "news",
                "summary_zh": "整理本周代理工具的新动向。",
                "tags": ["Agent", "Tooling"],
                "importance": 3,
            },
        ]
        if tags:
            articles = [article for article in articles if any(tag in article["tags"] for tag in tags)]
        if category:
            articles = [article for article in articles if article["source_category"] == category]
        if min_importance > 1:
            articles = [article for article in articles if article["importance"] >= min_importance]
        if q:
            term = q.casefold()
            articles = [
                article
                for article in articles
                if term in article["title"].casefold() or term in article["summary_zh"].casefold()
            ]
        if sort == "published":
            articles.sort(key=lambda item: item["published"], reverse=True)
        else:
            articles.sort(key=lambda item: item["importance"], reverse=True)
        by_category: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for article in articles:
            by_category[article["source_category"]] = by_category.get(article["source_category"], 0) + 1
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

    async def run_pipeline_async(self, progress_callback=None) -> dict:
        if progress_callback is not None:
            progress_callback({"stage": "fetching", "message": "Fetching feeds"})
        return {"result": "success"}

    def get_latest_github_trending(self, **kwargs) -> dict | None:
        _ = kwargs
        return self.get_github_trending_by_date("2026-04-15", **kwargs)

    def get_github_trending_by_date(self, date: str, **kwargs) -> dict | None:
        _ = kwargs
        return {
            "date": date,
            "generated_at": f"{date}T10:00:00+08:00",
            "stats": {
                "total": 1,
                "by_category": {"llm": 1},
                "by_language": {"Python": 1},
            },
            "projects": [
                {
                    "id": "acme/alpha",
                    "full_name": "acme/alpha",
                    "description": "Alpha helper",
                    "description_zh": "Alpha 助手",
                    "html_url": "https://github.com/acme/alpha",
                    "homepage": None,
                    "stars": 1200,
                    "forks": 32,
                    "open_issues": 4,
                    "language": "Python",
                    "topics": ["llm"],
                    "category": "llm",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-04-15T08:00:00Z",
                    "pushed_at": "2026-04-15T08:00:00Z",
                    "owner_avatar": "",
                    "owner_type": "Organization",
                    "license": "MIT",
                    "stars_today": 25,
                    "stars_weekly": 180,
                    "trend": "rising",
                }
            ],
        }

    async def run_github_fetch_async(self, progress_callback=None) -> dict:
        if progress_callback is not None:
            progress_callback({"stage": "searching", "message": "Searching topic: llm"})
        return {
            "outcome": "success",
            "reason": None,
            "snapshot": self.get_github_trending_by_date("2026-04-15"),
            "partial_path": None,
        }


def _read_resource_text(path: str) -> str:
    handle = QFile(path)
    assert handle.open(QIODevice.ReadOnly), f"unable to open resource: {path}"
    try:
        return bytes(handle.readAll()).decode("utf-8")
    finally:
        handle.close()


def test_qrc_manifest_and_bundle_exist_on_disk() -> None:
    assert QRC_PATH.is_file()
    assert RESOURCE_BUNDLE_PATH.is_file()


def test_qrc_registers_main_qml_and_controls_conf() -> None:
    main_qml = _read_resource_text(":/qt/qml/AIDaily/Desktop/Main.qml")
    controls_conf = _read_resource_text(":/qtquickcontrols2.conf")

    assert "ApplicationWindow" in main_qml
    assert "Style=Basic" in controls_conf


def test_qml_runtime_loads_root_window() -> None:
    runtime = create_qml_runtime(show=False)
    try:
        root = runtime.root_object
        assert root is not None
        assert root.objectName() == "desktopQmlWindow"
        assert root.property("title") == "AI Daily"
        assert QML_MAIN_URL.toString().startswith("qrc:/")
        assert QQuickStyle.name() in {DEFAULT_QUICK_STYLE, "Fusion"}
    finally:
        runtime.close()


def test_qml_runtime_uses_resource_import_root() -> None:
    runtime = create_qml_runtime(show=False)
    try:
        assert "qrc:/qt/qml" in runtime.engine.importPathList()
    finally:
        runtime.close()


def test_shell_switches_to_real_github_workspace() -> None:
    runtime = create_qml_runtime(show=False, services=FakeServices())
    try:
        runtime.shell.selectWorkspace("github-trends")
        runtime.app.processEvents()
        runtime.app.processEvents()
        root = runtime.root_object
        assert root is not None
        assert root.findChild(QObject, "githubTrendsPage") is not None
        assert root.findChild(QObject, "githubSnapshotList") is not None
        assert root.findChild(QObject, "githubProjectList") is not None
        assert root.findChild(QObject, "githubDetailPanel") is not None
        assert root.findChild(QObject, "githubApplyFiltersButton") is not None
    finally:
        runtime.close()


def test_shell_switches_to_real_ai_daily_workspace() -> None:
    runtime = create_qml_runtime(show=False, services=FakeServices())
    try:
        runtime.shell.selectWorkspace("ai-daily")
        runtime.app.processEvents()
        runtime.app.processEvents()
        root = runtime.root_object
        assert root is not None
        assert root.findChild(QObject, "aiDailyWorkspace") is not None
        assert root.findChild(QObject, "aiDailyArchiveList") is not None
        assert root.findChild(QObject, "aiDailyArticleList") is not None
        assert root.findChild(QObject, "aiDailyDetailPanel") is not None
        assert root.findChild(QObject, "aiDailyOpenArticleButton") is not None
    finally:
        runtime.close()
