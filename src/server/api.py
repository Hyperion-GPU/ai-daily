import asyncio
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable

from dateutil import parser as date_parser
from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Query

from main import load_config, run_pipeline
from src.github import GitHubTrendingFetcher

from .loader import list_dates, list_github_dates, load_digest, load_github_trending, load_index
from .schemas import (
    DateListResponse,
    DigestResponse,
    GitHubDateListResponse,
    GitHubFetchRunResponse,
    GitHubFetchStatusResponse,
    GitHubTrendingResponse,
    PipelineRunResponse,
    PipelineStatusResponse,
)

_GITHUB_SORT_OPTIONS = {"stars", "stars_today", "stars_weekly", "updated"}
_GITHUB_TREND_OPTIONS = {"rising", "hot", "stable"}

router = APIRouter(prefix="/api")


@dataclass
class BackgroundJobState:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    task: asyncio.Task | None = None
    running: bool = False
    last_run: str | None = None
    error: str | None = None
    last_outcome: str | None = None
    progress: dict | None = None

    def reset(self) -> None:
        self.task = None
        self.running = False
        self.last_run = None
        self.error = None
        self.last_outcome = None
        self.progress = None

    def update_progress(self, update: dict) -> None:
        current = dict(self.progress or {})
        current.update(update)
        self.progress = current

    def mark_started(self, initial_progress: dict) -> None:
        self.running = True
        self.error = None
        self.last_outcome = None
        self.progress = dict(initial_progress)

    def mark_finished(self, *, last_outcome: str, error: str | None = None, progress: dict | None = None) -> None:
        self.running = False
        self.last_run = datetime.now(timezone.utc).isoformat()
        self.last_outcome = last_outcome
        self.error = error
        if progress is not None:
            self.progress = dict(progress)
        self.task = None

    def snapshot(self) -> dict:
        return {
            "running": self.running,
            "last_run": self.last_run,
            "error": self.error,
            "last_outcome": self.last_outcome,
            "progress": dict(self.progress) if isinstance(self.progress, dict) else self.progress,
        }

    async def start(
        self,
        *,
        create_runner: Callable[[], Awaitable[object]],
        initial_progress: dict,
        conflict_detail: str,
        resolve_success_outcome: Callable[[object], str] | None = None,
    ) -> None:
        async with self.lock:
            if self.running:
                raise HTTPException(status_code=409, detail=conflict_detail)

            self.mark_started(initial_progress)
            self.task = asyncio.create_task(
                self._run(create_runner=create_runner, resolve_success_outcome=resolve_success_outcome)
            )

    async def _run(
        self,
        *,
        create_runner: Callable[[], Awaitable[object]],
        resolve_success_outcome: Callable[[object], str] | None,
    ) -> None:
        try:
            result = await create_runner()
        except Exception as exc:  # pragma: no cover
            self.mark_finished(
                last_outcome="error",
                error=str(exc),
                progress={
                    **(self.progress or {}),
                    "stage": "error",
                    "message": str(exc),
                },
            )
            return

        success_outcome = resolve_success_outcome(result) if resolve_success_outcome else "success"
        self.mark_finished(last_outcome=success_outcome, error=None)


_pipeline_state = BackgroundJobState()
_github_fetch_state = BackgroundJobState()


def _reset_pipeline_state() -> None:
    _pipeline_state.reset()


def _update_pipeline_progress(update: dict) -> None:
    _pipeline_state.update_progress(update)


def _reset_github_fetch_state() -> None:
    _github_fetch_state.reset()


def _update_github_fetch_progress(update: dict) -> None:
    _github_fetch_state.update_progress(update)


def _published_sort_key(article: dict) -> datetime:
    published = article.get("published")
    if not published:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        parsed = date_parser.parse(str(published))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _updated_sort_key(project: dict) -> datetime:
    updated = project.get("updated_at")
    if not updated:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        parsed = date_parser.parse(str(updated))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _sort_metric_value(project: dict, key: str) -> int:
    value = project.get(key)
    return int(value) if value is not None else -1


def _normalize_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalize_language_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _normalize_non_negative_int(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) and value >= 0 else default


def _normalize_sort(value: object) -> str:
    return value if isinstance(value, str) and value in _GITHUB_SORT_OPTIONS else "stars"


def _normalize_trend(value: object) -> str | None:
    return value if isinstance(value, str) and value in _GITHUB_TREND_OPTIONS else None


def _filter_github_snapshot(
    data: dict,
    *,
    category: str | None,
    languages: list[str],
    min_stars: int,
    sort: str,
    q: str | None,
    trend: str | None,
) -> dict:
    projects = list(data.get("projects", []))

    if category:
        projects = [project for project in projects if project.get("category") == category]
    if languages:
        normalized_languages = {language.casefold() for language in languages}
        projects = [
            project
            for project in projects
            if isinstance(project.get("language"), str)
            and project["language"].casefold() in normalized_languages
        ]
    if min_stars > 0:
        projects = [project for project in projects if int(project.get("stars", 0) or 0) >= min_stars]
    if trend:
        projects = [project for project in projects if project.get("trend") == trend]
    if q:
        q_normalized = q.casefold()
        projects = [
            project
            for project in projects
            if q_normalized in str(project.get("full_name", "")).casefold()
            or q_normalized in str(project.get("description", "")).casefold()
            or q_normalized in str(project.get("description_zh", "")).casefold()
        ]

    if sort == "updated":
        projects = sorted(projects, key=_updated_sort_key, reverse=True)
    elif sort == "stars_today":
        projects = sorted(projects, key=lambda project: _sort_metric_value(project, "stars_today"), reverse=True)
    elif sort == "stars_weekly":
        projects = sorted(projects, key=lambda project: _sort_metric_value(project, "stars_weekly"), reverse=True)
    else:
        projects = sorted(projects, key=lambda project: int(project.get("stars", 0) or 0), reverse=True)

    by_category = Counter(
        project.get("category")
        for project in projects
        if isinstance(project.get("category"), str) and project.get("category")
    )
    by_language = Counter(
        project.get("language")
        for project in projects
        if isinstance(project.get("language"), str) and project.get("language")
    )

    return {
        "date": data["date"],
        "generated_at": data["generated_at"],
        "stats": {
            "total": len(projects),
            "by_category": dict(by_category),
            "by_language": dict(by_language),
        },
        "projects": projects,
    }


@router.get("/dates", response_model=DateListResponse)
def get_dates():
    date_strings = list_dates()
    index_entries = load_index() or []
    stats_by_date = {
        entry.get("date"): entry
        for entry in index_entries
        if isinstance(entry.get("date"), str)
    }
    dates = []
    for date in date_strings:
        index_entry = stats_by_date.get(date)
        if index_entry:
            total = index_entry.get("total", 0)
            by_category = index_entry.get("by_category", {})
        else:
            digest = load_digest(date)
            stats = digest.get("stats", {}) if digest else {}
            total = stats.get("total", 0)
            by_category = stats.get("by_category", {})
        dates.append(
            {
                "date": date,
                "total": total,
                "by_category": by_category,
            }
        )
    return {"dates": dates, "latest": date_strings[0] if date_strings else None}


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline_endpoint():
    await _pipeline_state.start(
        create_runner=lambda: run_pipeline(load_config(), progress_callback=_update_pipeline_progress),
        initial_progress={
            "stage": "starting",
            "message": "Starting pipeline",
            "current": 0,
            "total": None,
            "candidates": 0,
            "selected": 0,
            "processed": 0,
            "report_articles": None,
        },
        conflict_detail="Pipeline is already running",
        resolve_success_outcome=lambda result: "no_new_items" if result.get("result") == "no_new_items" else "success",
    )

    return {"status": "started"}


@router.get("/pipeline/status", response_model=PipelineStatusResponse)
def get_pipeline_status():
    return _pipeline_state.snapshot()


@router.get("/github/dates", response_model=GitHubDateListResponse)
def get_github_dates():
    date_strings = list_github_dates()
    return {"dates": date_strings, "latest": date_strings[0] if date_strings else None}


@router.post("/github/fetch", response_model=GitHubFetchRunResponse)
async def run_github_fetch_endpoint():
    await _github_fetch_state.start(
        create_runner=lambda: GitHubTrendingFetcher(load_config()).run(progress_callback=_update_github_fetch_progress),
        initial_progress={
            "stage": "starting",
            "message": "Starting GitHub trending fetch",
            "current": 0,
            "total": None,
            "topics_done": 0,
            "topics_total": None,
            "projects_found": 0,
            "projects_new": 0,
        },
        conflict_detail="Fetch is already running",
    )

    return {"status": "started"}


@router.get("/github/fetch/status", response_model=GitHubFetchStatusResponse)
async def get_github_fetch_status():
    return _github_fetch_state.snapshot()


@router.get("/github/trending", response_model=GitHubTrendingResponse)
def get_latest_github_trending(
    category: str | None = None,
    language: list[str] = Query(default=[]),
    min_stars: int = Query(default=0, ge=0),
    sort: str = Query(default="stars", pattern="^(stars|stars_today|stars_weekly|updated)$"),
    q: str | None = None,
    trend: str | None = Query(default=None, pattern="^(rising|hot|stable)$"),
):
    dates = list_github_dates()
    if not dates:
        raise HTTPException(status_code=404, detail="No GitHub trending snapshots found")
    return get_github_trending_by_date(
        dates[0],
        category=_normalize_optional_str(category),
        language=_normalize_language_list(language),
        min_stars=_normalize_non_negative_int(min_stars),
        sort=_normalize_sort(sort),
        q=_normalize_optional_str(q),
        trend=_normalize_trend(trend),
    )


@router.get("/github/trending/{date}", response_model=GitHubTrendingResponse)
def get_github_trending_by_date(
    date: str = FastAPIPath(pattern=r"^\d{4}-\d{2}-\d{2}$"),
    category: str | None = None,
    language: list[str] = Query(default=[]),
    min_stars: int = Query(default=0, ge=0),
    sort: str = Query(default="stars", pattern="^(stars|stars_today|stars_weekly|updated)$"),
    q: str | None = None,
    trend: str | None = Query(default=None, pattern="^(rising|hot|stable)$"),
):
    data = load_github_trending(date)
    if data is None:
        raise HTTPException(status_code=404, detail=f"GitHub trending snapshot for {date} not found")

    return _filter_github_snapshot(
        data,
        category=_normalize_optional_str(category),
        languages=_normalize_language_list(language),
        min_stars=_normalize_non_negative_int(min_stars),
        sort=_normalize_sort(sort),
        q=_normalize_optional_str(q),
        trend=_normalize_trend(trend),
    )


@router.get("/digest/{date}", response_model=DigestResponse)
def get_digest(
    date: str,
    tags: list[str] = Query(default=[]),
    category: str | None = None,
    min_importance: int = Query(default=1, ge=1, le=5),
    sort: str = Query(default="importance", pattern="^(importance|published)$"),
    q: str | None = None,
):
    data = load_digest(date)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Digest for {date} not found")

    articles = data["articles"]

    if tags:
        articles = [article for article in articles if any(tag in article["tags"] for tag in tags)]
    if category:
        articles = [article for article in articles if article["source_category"] == category]
    if min_importance > 1:
        articles = [article for article in articles if article["importance"] >= min_importance]
    if q:
        q_normalized = q.casefold()
        articles = [
            article
            for article in articles
            if q_normalized in str(article.get("title", "")).casefold()
            or q_normalized in str(article.get("summary_zh", "")).casefold()
        ]

    if sort == "published":
        articles = sorted(articles, key=_published_sort_key, reverse=True)
    else:
        articles = sorted(articles, key=lambda article: article.get("importance", 0), reverse=True)

    by_category = Counter(article["source_category"] for article in articles)
    by_tag = Counter(tag for article in articles for tag in article["tags"])

    return {
        "date": data["date"],
        "generated_at": data["generated_at"],
        "stats": {
            "total": len(articles),
            "by_category": dict(by_category),
            "by_tag": dict(by_tag),
        },
        "articles": articles,
    }
