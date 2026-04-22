from __future__ import annotations

import asyncio
import copy
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("AI_DAILY_QML_STYLE", "Basic")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuickTest import QUICK_TEST_MAIN_WITH_SETUP

from src.desktop.facades import DigestWorkspaceFacade, GithubWorkspaceFacade, SettingsFacade, ShellFacade
from src.desktop.qml_app import QML_IMPORT_ROOT, register_qml_resources

register_qml_resources()


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
        path = Path(tempfile.gettempdir()) / "ai-daily-qml-tests"
        path.mkdir(parents=True, exist_ok=True)
        return path


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
        self.github_dates = ["2026-04-15", "2026-04-14"]
        self.github_snapshots = {
            "2026-04-15": {
                "date": "2026-04-15",
                "generated_at": "2026-04-15T10:00:00+08:00",
                "stats": {
                    "total": 2,
                    "by_category": {"llm": 1, "agent": 1},
                    "by_language": {"Python": 1, "TypeScript": 1},
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
                    },
                    {
                        "id": "acme/beta",
                        "full_name": "acme/beta",
                        "description": "Beta helper",
                        "description_zh": "",
                        "html_url": "https://github.com/acme/beta",
                        "homepage": None,
                        "stars": 980,
                        "forks": 12,
                        "open_issues": 2,
                        "language": "TypeScript",
                        "topics": ["agent"],
                        "category": "agent",
                        "created_at": "2026-01-02T00:00:00Z",
                        "updated_at": "2026-04-15T07:00:00Z",
                        "pushed_at": "2026-04-15T07:00:00Z",
                        "owner_avatar": "",
                        "owner_type": "Organization",
                        "license": "Apache-2.0",
                        "stars_today": 15,
                        "stars_weekly": 120,
                        "trend": "hot",
                    },
                ],
            }
        }
        self.github_fetch_result = self._build_github_fetch_result("success")
        self.digest_dates = ["2026-04-15", "2026-04-14"]
        self.digest_articles = {
            "2026-04-15": [
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
            ],
            "2026-04-14": [
                {
                    "id": "digest-3",
                    "title": "Research digest on multimodal agents",
                    "url": "https://example.com/research",
                    "published": "2026-04-14T09:00:00Z",
                    "source_name": "ArXiv",
                    "source_category": "arxiv",
                    "summary_zh": "多模态代理论文摘要与重点整理。",
                    "tags": ["Agent", "Research"],
                    "importance": 4,
                }
            ],
        }
        self._post_fetch_digest_date = "2026-04-16"
        self._post_fetch_digest_articles = [
            {
                "id": "digest-4",
                "title": "Fresh digest after fetch",
                "url": "https://example.com/fresh",
                "published": "2026-04-16T09:15:00Z",
                "source_name": "OpenAI",
                "source_category": "official",
                "summary_zh": "抓取成功后应自动暴露最新归档。",
                "tags": ["OpenAI", "Desktop"],
                "importance": 5,
            }
        ]
        self._base_digest_dates = copy.deepcopy(self.digest_dates)
        self._base_digest_articles = copy.deepcopy(self.digest_articles)

    def reset_digest_state(self) -> None:
        self.digest_dates = copy.deepcopy(self._base_digest_dates)
        self.digest_articles = copy.deepcopy(self._base_digest_articles)

    def _build_github_fetch_result(self, outcome: str, reason: str | None = None) -> dict:
        snapshot = copy.deepcopy(self.github_snapshots["2026-04-15"]) if outcome == "success" else None
        return {
            "outcome": outcome,
            "reason": reason,
            "snapshot": snapshot,
            "partial_path": None if outcome == "success" else str(REPO_ROOT / "output" / "github.partial.json"),
        }

    def configure_github_fetch_result(self, outcome: str, reason: str | None = None) -> None:
        self.github_fetch_result = self._build_github_fetch_result(outcome, reason)

    def reset_github_fetch_state(self) -> None:
        self.github_fetch_result = self._build_github_fetch_result("success")

    def current_config(self) -> dict:
        return copy.deepcopy(self._config)

    def replace_config(self, config: dict) -> None:
        self._config = copy.deepcopy(config)

    def get_github_dates(self) -> dict:
        return {"dates": list(self.github_dates), "latest": self.github_dates[0]}

    def get_dates(self) -> dict:
        items = []
        for date in self.digest_dates:
            articles = self.digest_articles.get(date, [])
            by_category: dict[str, int] = {}
            for article in articles:
                key = str(article.get("source_category", "") or "")
                by_category[key] = by_category.get(key, 0) + 1
            items.append({"date": date, "total": len(articles), "by_category": by_category})
        return {"dates": items, "latest": self.digest_dates[0] if self.digest_dates else None}

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
        articles = copy.deepcopy(self.digest_articles.get(date, []))
        if category:
            articles = [article for article in articles if article["source_category"] == category]
        if tags:
            normalized = {tag.casefold() for tag in tags}
            articles = [
                article
                for article in articles
                if any(str(tag).casefold() in normalized for tag in article.get("tags", []))
            ]
        if min_importance > 1:
            articles = [article for article in articles if int(article.get("importance", 0) or 0) >= min_importance]
        if q:
            query = q.casefold()
            articles = [
                article
                for article in articles
                if query in str(article.get("title", "")).casefold()
                or query in str(article.get("summary_zh", "")).casefold()
            ]
        if sort == "published":
            articles.sort(key=lambda item: str(item.get("published", "")), reverse=True)
        else:
            articles.sort(key=lambda item: int(item.get("importance", 0) or 0), reverse=True)
        by_category: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        for article in articles:
            by_category[article["source_category"]] = by_category.get(article["source_category"], 0) + 1
            for tag in article.get("tags", []):
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
            await asyncio.sleep(0.3)
        if self._post_fetch_digest_date not in self.digest_dates:
            self.digest_dates = [self._post_fetch_digest_date, *self.digest_dates]
            self.digest_articles[self._post_fetch_digest_date] = copy.deepcopy(self._post_fetch_digest_articles)
        return {"result": "success", "article_count": len(self._post_fetch_digest_articles)}

    def get_latest_github_trending(
        self,
        *,
        category: str | None,
        language: list[str],
        min_stars: int,
        sort: str,
        q: str | None,
        trend: str | None,
    ) -> dict | None:
        latest = self.github_dates[0] if self.github_dates else None
        if latest is None:
            return None
        return self.get_github_trending_by_date(
            latest,
            category=category,
            language=language,
            min_stars=min_stars,
            sort=sort,
            q=q,
            trend=trend,
        )

    def get_github_trending_by_date(
        self,
        date: str,
        *,
        category: str | None,
        language: list[str],
        min_stars: int,
        sort: str,
        q: str | None,
        trend: str | None,
    ) -> dict | None:
        snapshot = copy.deepcopy(self.github_snapshots.get(date))
        if snapshot is None:
            return None
        projects = list(snapshot["projects"])
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
        if q:
            query = q.casefold()
            projects = [
                project
                for project in projects
                if query in str(project.get("full_name", "")).casefold()
                or query in str(project.get("description", "")).casefold()
                or query in str(project.get("description_zh", "")).casefold()
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
        if progress_callback is not None:
            progress_callback({"stage": "searching", "message": "Searching topic: llm"})
            await asyncio.sleep(0.3)
        return copy.deepcopy(self.github_fetch_result)


class QuickTestSetup(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._services = FakeServices()
        self._shell = ShellFacade()
        self._settings = SettingsFacade(lambda: self._services)
        self._digest = DigestWorkspaceFacade(lambda: self._services)
        self._github = GithubWorkspaceFacade(lambda: self._services)
        self._settings.saved.connect(self._digest.markStale)
        self._settings.saved.connect(self._github.markStale)
        self._shell.currentWorkspaceChanged.connect(self._reload_github_if_needed)
        self._shell.currentWorkspaceChanged.connect(self._reload_digest_if_needed)

    @Slot()
    def resetDigestState(self) -> None:
        self._services.reset_digest_state()
        self._digest.reload()

    @Slot()
    def resetGithubFetchState(self) -> None:
        self._services.reset_github_fetch_state()

    @Slot(str, str)
    def configureGithubFetchResult(self, outcome: str, reason: str) -> None:
        self._services.configure_github_fetch_result(outcome, reason or None)

    def _reload_digest_if_needed(self) -> None:
        if self._shell.currentWorkspace == "ai-daily" and (self._digest.stale or not self._digest.currentDate):
            self._digest.reload()

    def _reload_github_if_needed(self) -> None:
        if self._shell.currentWorkspace == "github-trends" and (self._github.stale or not self._github.currentDate):
            self._github.reload()

    @Slot(QQmlEngine)
    def qmlEngineAvailable(self, engine: QQmlEngine) -> None:
        engine.addImportPath(QML_IMPORT_ROOT)
        engine.rootContext().setContextProperty("appShellFacade", self._shell)
        engine.rootContext().setContextProperty("desktopSettingsFacade", self._settings)
        engine.rootContext().setContextProperty("desktopDigestFacade", self._digest)
        engine.rootContext().setContextProperty("desktopGithubFacade", self._github)
        engine.rootContext().setContextProperty("desktopTestSetup", self)


if __name__ == "__main__":
    test_dir = Path(__file__).resolve().parent
    os.chdir(test_dir)
    os.environ.setdefault("QUICK_TEST_SOURCE_DIR", ".")
    argv = list(sys.argv)
    if "-input" not in argv:
        argv.extend(["-input", "."])
    if "-o" not in argv:
        argv.extend(["-o", "-,txt", "-v1"])
    raise SystemExit(
        QUICK_TEST_MAIN_WITH_SETUP(
            "desktop_qml",
            QuickTestSetup,
            argv,
            ".",
        )
    )
