import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable

from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Query

from main import load_config, run_pipeline
from src.github import GitHubTrendingFetcher
from src.services import ApplicationServices

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

router = APIRouter(prefix="/api")


def _build_services(config: dict | None = None) -> ApplicationServices:
    return ApplicationServices(
        config=config if config is not None else load_config(),
        list_dates_fn=list_dates,
        load_index_fn=load_index,
        load_digest_fn=load_digest,
        list_github_dates_fn=list_github_dates,
        load_github_trending_fn=load_github_trending,
        load_config_fn=load_config,
        run_pipeline_fn=run_pipeline,
        github_fetcher_factory=GitHubTrendingFetcher,
    )


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


def _normalize_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalize_language_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


@router.get("/dates", response_model=DateListResponse)
def get_dates():
    return _build_services().get_dates()


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline_endpoint():
    services = _build_services()
    await _pipeline_state.start(
        create_runner=lambda: services.run_pipeline_async(progress_callback=_update_pipeline_progress),
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
    return _build_services().get_github_dates()


@router.post("/github/fetch", response_model=GitHubFetchRunResponse)
async def run_github_fetch_endpoint():
    services = _build_services()
    await _github_fetch_state.start(
        create_runner=lambda: services.run_github_fetch_async(progress_callback=_update_github_fetch_progress),
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
    result = _build_services().get_latest_github_trending(
        category=_normalize_optional_str(category),
        language=_normalize_language_list(language),
        min_stars=min_stars,
        sort=sort,
        q=_normalize_optional_str(q),
        trend=_normalize_optional_str(trend),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No GitHub trending snapshots found")
    return result


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
    result = _build_services().get_github_trending_by_date(
        date,
        category=_normalize_optional_str(category),
        language=_normalize_language_list(language),
        min_stars=min_stars,
        sort=sort,
        q=_normalize_optional_str(q),
        trend=_normalize_optional_str(trend),
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"GitHub trending snapshot for {date} not found")
    return result


@router.get("/digest/{date}", response_model=DigestResponse)
def get_digest(
    date: str,
    tags: list[str] = Query(default=[]),
    category: str | None = None,
    min_importance: int = Query(default=1, ge=1, le=5),
    sort: str = Query(default="importance", pattern="^(importance|published)$"),
    q: str | None = None,
):
    result = _build_services().get_digest(
        date,
        tags=tags,
        category=category,
        min_importance=min_importance,
        sort=sort,
        q=q,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Digest for {date} not found")
    return result
